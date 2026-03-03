import time
import uuid
import re
from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException
from backend.utils.logging import log_inference_telemetry
from backend.tools.youtube_backup_downloader import run_youtube_backup


async def handle_youtube_backup(user_text: str) -> dict:
    url_match = re.search(r"(https?://\S+)", user_text)
    if not url_match:
        raise HTTPException(status_code=400, detail="No valid YouTube URL found")
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
