"""Structured JSON logging configuration and telemetry emitters."""

import json
import logging
import logging.config
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        if record.exc_info:
            import traceback

            log_record["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        if "response" in log_record and isinstance(log_record["response"], str):
            log_record["response"] = log_record["response"].strip()

        return (
            "\n"
            + json.dumps(
                log_record,
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )


# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JsonFormatter,
        },
    },
    "handlers": {
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "app.log"),
            "encoding": "utf-8",
            "maxBytes": 10_000_000,
            "backupCount": 5,
        },
        "inference_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "inference.log"),
            "encoding": "utf-8",
            "maxBytes": 10_000_000,
            "backupCount": 5,
        },
        "telemetry_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "telemetry.jsonl"),
            "encoding": "utf-8",
            "maxBytes": 10_000_000,
            "backupCount": 5,
        },
    },
    "loggers": {
        "services.inference": {
            "handlers": ["inference_file", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "telemetry": {
            "handlers": ["telemetry_file", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["app_file"],
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)


inference_logger = logging.getLogger("services.inference")
telemetry_logger = logging.getLogger("telemetry")
app_logger = logging.getLogger("app")


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------


def _sanitize(obj: Any):
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


# ---------------------------------------------------------
# Inference Logging
# ---------------------------------------------------------


def log_inference_request(
    *,
    request_id: str,
    prompt: str,
    model_name: str,
    strategy: str | None = None,
):
    inference_logger.info(
        "inference_request_received",
        extra={
            "extra_data": {
                "request_id": request_id,
                "prompt": prompt,
                "model_used": model_name,
                "strategy": strategy,
                "event": "request_received",
            }
        },
    )


def log_inference_response(
    *,
    request_id: str,
    response_text: str,
    model_name: str,
    inference_process_time: float,
):
    inference_logger.info(
        "inference_response_generated",
        extra={
            "extra_data": {
                "request_id": request_id,
                "response": response_text,
                "model_used": model_name,
                "inference_process_time": inference_process_time,
                "event": "response_generated",
            }
        },
    )


# ---------------------------------------------------------
# Telemetry Logging
# ---------------------------------------------------------


def log_inference_telemetry(
    *,
    request_id: str,
    model_used: str,
    task_type: str | None,
    inference_process_time: float,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
):
    tokens_per_second = (
        round(total_tokens / inference_process_time, 4)
        if inference_process_time > 0
        else None
    )

    payload = {
        "event": "inference_complete",
        "request_id": request_id,
        "model_used": model_used,
        "task_type": task_type,
        "inference_process_time": inference_process_time,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_per_second": tokens_per_second,
    }

    telemetry_logger.info(
        "telemetry_recorded",
        extra={"extra_data": _sanitize(payload)},
    )


def log_tool_execution_start(
    *,
    request_id: str,
    tool_name: str,
    started_at: str,
    input_data: dict[str, Any] | None = None,
):
    payload = {
        "event": "tool_execution_started",
        "request_id": request_id,
        "tool_name": tool_name,
        "started_at": started_at,
        "input": input_data or {},
    }

    telemetry_logger.info(
        "tool_execution_started",
        extra={"extra_data": _sanitize(payload)},
    )


def log_tool_execution_result(
    *,
    request_id: str,
    tool_name: str,
    started_at: str,
    finished_at: str,
    latency_seconds: float,
    output_data: dict[str, Any] | None = None,
):
    payload = {
        "event": "tool_execution_finished",
        "request_id": request_id,
        "tool_name": tool_name,
        "started_at": started_at,
        "finished_at": finished_at,
        "latency_seconds": latency_seconds,
        "output": output_data or {},
    }

    telemetry_logger.info(
        "tool_execution_finished",
        extra={"extra_data": _sanitize(payload)},
    )


def log_rag_index_access(
    *,
    request_id: str,
    query: str,
    top_k: int,
    index_path: str,
    retrieved_ids: list[int] | None = None,
):
    payload = {
        "event": "rag_index_accessed",
        "request_id": request_id,
        "query": query,
        "top_k": top_k,
        "index_path": index_path,
        "retrieved_ids": retrieved_ids or [],
        "retrieved_count": len(retrieved_ids or []),
    }

    telemetry_logger.info(
        "rag_index_accessed",
        extra={"extra_data": _sanitize(payload)},
    )
