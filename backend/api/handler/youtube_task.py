import time
import uuid
import re
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException
from backend.utils.logging import (
    log_inference_telemetry,
    log_tool_execution_start,
    log_tool_execution_result,
)
from backend.tools.youtube_backup_downloader import run_youtube_backup


async def handle_youtube_backup(
    user_text: str, target_folder: str = "target_folder"
) -> dict:
    url_match = re.search(r"(https?://\S+)", user_text)
    if not url_match:
        raise HTTPException(status_code=400, detail="No valid YouTube URL found")
    url = url_match.group(1)
    request_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    log_tool_execution_start(
        request_id=request_id,
        tool_name="youtube_backup",
        started_at=started_at,
        input_data={"url": url, "target_folder": target_folder},
    )

    start = time.perf_counter()
    result = await run_in_threadpool(run_youtube_backup, url, target_folder)
    latency = time.perf_counter() - start

    finished_at = datetime.now(timezone.utc).isoformat()

    log_tool_execution_result(
        request_id=request_id,
        tool_name="youtube_backup",
        started_at=started_at,
        finished_at=finished_at,
        latency_seconds=latency,
        output_data={
            "status": result.get("status"),
            "download_folder": result.get("download_folder"),
            "downloaded_count": result.get("downloaded_count", 0),
            "downloaded_songs": result.get("downloaded_songs", []),
        },
    )
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
