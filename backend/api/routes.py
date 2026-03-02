"""HTTP endpoints for chat inference and request telemetry.

The /chat endpoint validates payloads, routes requests to the most suitable
model/strategy, optionally injects RAG context, and records structured logs.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from backend.services.inference import run_routed_inference
from backend.services.router import route_request
from backend.utils.logging import (
    log_inference_request,
    log_inference_response,
    log_inference_telemetry,
)
import json
import logging
import time
import uuid

# Import LocalRAG instance from rag.py
from backend.services.rag import LocalRAG

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialized during startup background ingestion in app.main.
rag_engine: LocalRAG | None = None


def set_rag_engine(engine: LocalRAG) -> None:
    """Inject the ready-to-use RAG engine once ingestion completes."""
    global rag_engine
    rag_engine = engine


@router.post("/chat")
async def chat(request: Request):
    """Handle chat requests end-to-end through routing + inference services."""
    logger.info("Received /chat request")

    # Read request body
    raw = await request.body()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON payload", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

    if "messages" not in body:
        raise HTTPException(
            status_code=400, detail="Missing 'messages' in request body"
        )

    messages = body["messages"]

    if not isinstance(messages, list):
        raise HTTPException(status_code=400, detail="'messages' must be a list")

    for msg in messages:
        if not isinstance(msg, dict):
            raise HTTPException(status_code=400, detail="Each message must be a dict")
        if "role" not in msg or "content" not in msg:
            raise HTTPException(
                status_code=400, detail="Each message must contain role and content"
            )

    # Determine routing first
    routing = route_request(messages)
    model_name = routing.get("target_model")

    if routing.get("task_type") == "youtube_backup":
        from backend.tools.youtube_backup_downloader import run_youtube_backup
        import re

        user_text = messages[-1]["content"]
        url_match = re.search(r"(https?://\S+)", user_text)

        if not url_match:
            raise HTTPException(
                status_code=400,
                detail="No valid YouTube URL found in request.",
            )

        url = url_match.group(1)

        start = time.perf_counter()
        result = await run_in_threadpool(run_youtube_backup, url)
        latency = time.perf_counter() - start

        request_id = str(uuid.uuid4())

        log_inference_telemetry(
            request_id=request_id,
            model_used="tool:youtube_backup",
            task_type="youtube_backup",
            inference_process_time=latency,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )

        return {"response": f"Download status: {result.get('status')}"}

    # RAG retrieval only if required
    if routing.get("requires_rag"):
        if rag_engine is None:
            logger.info("RAG not ready yet; responding without retrieved context")
            raise HTTPException(
                status_code=503,
                detail="RAG store not ready yet. Please retry in a moment.",
            )

        user_query = messages[-1]["content"]
        retrieved_chunks = rag_engine.search(user_query, top_k=4)
        context_block = "\n\n".join(retrieved_chunks)
        messages = [
            {
                "role": "system",
                "content": "Use the following context to answer the question.\n\n"
                + context_block,
            }
        ] + messages
    print(rag_engine.index.d)
    request_id = str(uuid.uuid4())
    prompt_text = "\n".join([m["content"] for m in messages])

    log_inference_request(
        request_id=request_id,
        prompt=prompt_text,
        model_name=model_name,
        strategy=routing.get("chunk_strategy"),
    )

    start = time.perf_counter()

    response = await run_in_threadpool(
        run_routed_inference,
        model_name=model_name,
        messages=messages,
        routing=routing,
    )

    latency = time.perf_counter() - start
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    response_text = response.get("text", "")

    log_inference_response(
        request_id=request_id,
        response_text=response_text,
        model_name=model_name,
        inference_process_time=latency,
    )

    log_inference_telemetry(
        request_id=request_id,
        model_used=model_name,
        task_type=routing.get("task_type"),
        inference_process_time=latency,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
    )

    logger.info("Generated response successfully")
    return {"response": response_text}
