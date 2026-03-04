"""Hybrid RAG manager (DB as source of truth, FAISS/.docs as fast cache)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from sqlalchemy import or_

import backend.config as config
from backend.model.models import Chunk, Document
from backend.services.embeddings import get_embedding_service
from backend.services.rag.document_loader import DocumentPayload, iter_chunk_records, load_documents
from backend.services.vector_store import FaissVectorStore
from backend.utils.logging import log_db_query, log_rag_index_access, log_rag_indexing
from db.session import SessionLocal


class LocalRAG:
    """Keeps document metadata in DB and vectors in FAISS for fast retrieval."""

    def __init__(self) -> None:
        self.embedder = get_embedding_service()
        dim = int(self.embedder.embed_texts(["dimension_check"]).shape[1])
        self.vector_store = FaissVectorStore(embedding_dim=dim, index_path=config.RAG_INDEX_PATH)
        self.docs_path = Path(config.RAG_DOCS_PATH)
        self.docs_cache = self._load_docs_cache()

    def _load_docs_cache(self) -> dict[str, dict]:
        if not self.docs_path.exists():
            return {}
        return json.loads(self.docs_path.read_text(encoding="utf-8"))

    def _save_docs_cache(self) -> None:
        self.docs_path.parent.mkdir(parents=True, exist_ok=True)
        self.docs_path.write_text(json.dumps(self.docs_cache, ensure_ascii=False), encoding="utf-8")

    def _upsert_document(self, session, payload: DocumentPayload) -> tuple[Document, bool]:
        started = time.perf_counter()
        doc = session.query(Document).filter(Document.path == payload.path).first()
        if doc is None:
            doc = Document(path=payload.path, checksum=payload.checksum, mtime=payload.mtime, namespace=payload.stable_id)
            session.add(doc)
            session.flush()
            log_db_query(operation="insert", table="files", filters={"path": payload.path}, rows=1, latency_seconds=time.perf_counter() - started)
            return doc, True

        changed = doc.checksum != payload.checksum
        doc.namespace = doc.namespace or payload.stable_id
        doc.mtime = payload.mtime
        doc.checksum = payload.checksum
        log_db_query(operation="select", table="files", filters={"path": payload.path}, rows=1, latency_seconds=time.perf_counter() - started)
        return doc, changed

    def _soft_delete_missing_documents(self, session, existing_paths: set[str]) -> None:
        docs = session.query(Document).filter(~Document.path.in_(existing_paths)).all()
        for doc in docs:
            for chunk in doc.chunks:
                chunk.deleted = True
                cache = self.docs_cache.get(str(chunk.id))
                if cache:
                    cache["deleted"] = True

    def _reindex_document(self, session, doc: Document, payload: DocumentPayload) -> None:
        started = time.perf_counter()
        stale_vector_ids = [c.vector_id for c in doc.chunks if c.vector_id]
        if stale_vector_ids:
            self.vector_store.remove(np.array(stale_vector_ids, dtype="int64"))
        for chunk in doc.chunks:
            chunk.deleted = True
            cache = self.docs_cache.get(str(chunk.id))
            if cache:
                cache["deleted"] = True

        chunks: list[str] = []
        embeddings_inputs: list[str] = []
        for _, chunk_text in iter_chunk_records(payload):
            chunks.append(chunk_text)
            embeddings_inputs.append(chunk_text)

        if not chunks:
            return

        embeddings = self.embedder.embed_texts(embeddings_inputs)
        chunk_models: list[Chunk] = []
        for index, chunk_text in enumerate(chunks):
            chunk = Chunk(document_id=doc.id, chunk_index=index, text=chunk_text, deleted=False)
            session.add(chunk)
            session.flush()
            chunk.vector_id = chunk.id
            chunk_models.append(chunk)
            self.docs_cache[str(chunk.id)] = {
                "path": doc.path,
                "text": chunk_text,
                "stable_id": doc.namespace,
                "deleted": False,
            }

        ids = np.array([chunk.id for chunk in chunk_models], dtype="int64")
        self.vector_store.add(embeddings, ids)
        log_rag_indexing(action="upsert", path=doc.path, stable_id=doc.namespace or "", checksum=payload.checksum, chunk_count=len(chunk_models), latency_seconds=time.perf_counter() - started)

    def sync(self) -> None:
        session = SessionLocal()
        try:
            docs = load_documents()
            seen_paths = {doc.path for doc in docs}
            self._soft_delete_missing_documents(session, seen_paths)

            for payload in docs:
                doc, changed = self._upsert_document(session, payload)
                if changed or any(chunk.deleted for chunk in doc.chunks):
                    self._reindex_document(session, doc, payload)

            session.commit()
            self.vector_store.save()
            self._save_docs_cache()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _search_db(self, session, query: str, top_k: int) -> list[Chunk]:
        started = time.perf_counter()
        like_query = f"%{query.strip()}%"
        rows = (
            session.query(Chunk)
            .filter(Chunk.deleted.is_(False))
            .filter(or_(Chunk.text.ilike(like_query), Chunk.text.ilike(f"%{query[:32]}%")))
            .limit(top_k)
            .all()
        )
        log_db_query(operation="select", table="chunks", filters={"query": query, "top_k": top_k}, rows=len(rows), latency_seconds=time.perf_counter() - started)
        return rows

    def search(self, query: str, top_k: int = config.RAG_TOP_K, request_id: str | None = None) -> list[str]:
        request_ref = request_id or "unknown"
        session = SessionLocal()
        try:
            started = time.perf_counter()
            db_rows = self._search_db(session, query, top_k)
            if db_rows:
                log_rag_index_access(request_id=request_ref, query=query, top_k=top_k, source="database", retrieved_ids=[row.id for row in db_rows], latency_seconds=time.perf_counter() - started)
                return [row.text for row in db_rows]

            query_emb = self.embedder.embed_texts([query])
            chunk_ids = self.vector_store.search(query_emb, top_k)

            chunk_rows = session.query(Chunk).filter(Chunk.id.in_(chunk_ids), Chunk.deleted.is_(False)).all() if chunk_ids else []
            if chunk_rows:
                text_by_id = {chunk.id: chunk.text for chunk in chunk_rows}
                ordered = [text_by_id[cid] for cid in chunk_ids if cid in text_by_id]
                log_rag_index_access(request_id=request_ref, query=query, top_k=top_k, source="index+database", retrieved_ids=chunk_ids, latency_seconds=time.perf_counter() - started)
                return ordered

            docs_hits = [self.docs_cache.get(str(cid), {}) for cid in chunk_ids]
            fallback_texts = [hit.get("text", "") for hit in docs_hits if hit and not hit.get("deleted")]
            log_rag_index_access(request_id=request_ref, query=query, top_k=top_k, source="index+docs", retrieved_ids=chunk_ids, latency_seconds=time.perf_counter() - started)
            return [text for text in fallback_texts if text]
        finally:
            session.close()

    def save(self) -> None:
        self.vector_store.save()
        self._save_docs_cache()
