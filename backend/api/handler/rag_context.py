from backend.services.rag.vector_manager import LocalRAG


def inject_rag_context(rag_engine: LocalRAG, messages: list, top_k: int = 4) -> list:
    user_query = messages[-1]["content"]
    retrieved_chunks = rag_engine.search(user_query, top_k=top_k)
    context_block = "\n\n".join(retrieved_chunks)
    return [
        {"role": "system", "content": f"Use the following context:\n\n{context_block}"}
    ] + messages
