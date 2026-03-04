"""Backwards-compatible RAG engine entrypoint."""

from backend.services.rag.vector_manager import LocalRAG


def build_rag_index() -> LocalRAG:
    rag = LocalRAG()
    rag.sync()
    return rag
