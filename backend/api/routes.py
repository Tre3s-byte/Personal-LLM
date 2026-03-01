from fastapi import APIRouter, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
from services.inference import run_routed_inference
from services.router import route_request
from utils.logging import (
    log_inference_request,
    log_inference_response,
    log_inference_telemetry,
)
import json
import logging
import time
import uuid

# Import LocalRAG instance from rag.py
from services.rag import LocalRAG, build_rag_index

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize RAG asynchronously (or at startup in main.py)
rag_engine: LocalRAG = build_rag_index()


@router.post("/chat")
async def chat(request: Request):
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

    # RAG retrieval only if required
    if routing.get("requires_rag"):
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
