from numbers import Integral
from backend.services.rag.vector_manager import LocalRAG
from backend.utils.logging import log_rag_index_access


def inject_rag_context(
    rag_engine: LocalRAG,
    messages: list,
    top_k: int = 4,
    request_id: str | None = None,
) -> list:
    user_query = messages[-1]["content"]
    retrieved_chunks = rag_engine.search(user_query, top_k=top_k)
    numeric_ids = [int(item) for item in retrieved_chunks if isinstance(item, Integral)]

    log_rag_index_access(
        request_id=request_id or "unknown",
        query=user_query,
        top_k=top_k,
        index_path=str(rag_engine.vector_store.index_path),
        retrieved_ids=numeric_ids,
    )

    context_block = "\n\n".join([str(chunk) for chunk in retrieved_chunks])
    return [
        {"role": "system", "content": f"Use the following context:\n\n{context_block}"}
    ] + messages
