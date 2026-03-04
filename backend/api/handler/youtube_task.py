import re
import uuid
import time
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from backend.api.handler import rag_context
from backend.services.inference.prompt_handler import run_routed_inference
from backend.utils.logging import (
    log_tool_execution_start,
    log_tool_execution_result,
    log_inference_telemetry,
)


async def handle_youtube_backup(
    user_text: str, target_folder: str = None, rag_engine=None
) -> dict:
    url_match = re.search(r"(https?://\S+)", user_text)
    if not url_match:
        raise HTTPException(status_code=400, detail="No valid YouTube URL found")
    url = url_match.group(1)
    request_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    # RAG context injection
    messages = [{"role": "user", "content": user_text}]
    if rag_engine:
        messages = rag_context.inject_rag_context(
            rag_engine, messages, request_id=request_id
        )

    # Build prompt for recommendation
    prompt_text = "\n".join([m["content"] for m in messages])
    system_prompt = (
        "You are a personal assistant. Use the provided RAG context to "
        "give a recommendation for storing the media, based on past indexed knowledge. "
        "Do NOT perform any downloads, only recommend a folder."
    )
    routed_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_text},
    ]

    # Run small/light model inference
    start = time.perf_counter()
    response = await run_in_threadpool(
        run_routed_inference,
        model_name="small",
        messages=routed_messages,
        routing={"task_type": "youtube_backup"},
    )
    latency = time.perf_counter() - start

    recommended_folder = response.get("response", target_folder or "Music")

    # Log recommendation
    log_tool_execution_start(
        request_id=request_id,
        tool_name="youtube_backup",
        started_at=started_at,
        input_data={"url": url, "user_text": user_text},
    )

    finished_at = datetime.now(timezone.utc).isoformat()
    log_tool_execution_result(
        request_id=request_id,
        tool_name="youtube_backup",
        started_at=started_at,
        finished_at=finished_at,
        latency_seconds=latency,
        output_data={"recommended_folder": recommended_folder},
    )

    log_inference_telemetry(
        request_id=request_id,
        model_used="small",
        task_type="youtube_backup",
        inference_process_time=latency,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    )

    return {"response": f"Recommended folder: {recommended_folder}"}
