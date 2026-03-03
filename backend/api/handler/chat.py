import time
import uuid
import logging
from fastapi import Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from backend.services.inference.prompt_handler import run_routed_inference
from backend.services.router import route_request
from backend.services.rag.vector_manager import LocalRAG
from backend.api.handler import validation, youtube_task, rag_context, inference_logger

logger = logging.getLogger(__name__)
rag_engine: LocalRAG | None = None


def set_rag_engine(engine: LocalRAG) -> None:
    """Inject the ready-to-use RAG engine once ingestion completes."""
    global rag_engine
    rag_engine = engine


async def handle_chat_request(request: Request):
    logger.info("Received /chat request")

    body = await validation.parse_request_body(request)
    messages = validation.validate_messages(body)

    routing = route_request(messages)
    model_name = routing.get("target_model")

    # YouTube task
    if routing.get("task_type") == "youtube_backup":
        return await youtube_task.handle_youtube_backup(messages[-1]["content"])

    # RAG injection
    if routing.get("requires_rag"):
        if rag_engine is None:
            raise HTTPException(status_code=503, detail="RAG store not ready yet")
        messages = rag_context.inject_rag_context(rag_engine, messages)

    # Logging and inference
    request_id = str(uuid.uuid4())
    prompt_text = "\n".join([m["content"] for m in messages])
    inference_logger.log_request(
        request_id, prompt_text, model_name, routing.get("chunk_strategy")
    )

    start = time.perf_counter()
    response = await run_in_threadpool(
        run_routed_inference, model_name=model_name, messages=messages, routing=routing
    )
    latency = time.perf_counter() - start

    response_text, usage = inference_logger.process_response(
        response, request_id, model_name, routing.get("task_type"), latency
    )

    logger.info("Generated response successfully")
    return {"response": response_text}
