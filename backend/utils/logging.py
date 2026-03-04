"""Centralized structured logging utilities."""

from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JsonFormatter(logging.Formatter):
    """Formatter that serializes all log records as a single JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra_data = getattr(record, "extra_data", None)
        if isinstance(extra_data, dict):
            payload.update(extra_data)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": JsonFormatter}},
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
            "filename": str(LOG_DIR / "telemetry.log"),
            "encoding": "utf-8",
            "maxBytes": 10_000_000,
            "backupCount": 5,
        },
        "rag_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "rag.log"),
            "encoding": "utf-8",
            "maxBytes": 10_000_000,
            "backupCount": 5,
        },
        "db_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "db.log"),
            "encoding": "utf-8",
            "maxBytes": 10_000_000,
            "backupCount": 5,
        },
    },
    "loggers": {
        "app": {"handlers": ["app_file"], "level": "INFO", "propagate": False},
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
        "rag": {"handlers": ["rag_file", "app_file"], "level": "INFO", "propagate": False},
        "db": {"handlers": ["db_file", "app_file"], "level": "INFO", "propagate": False},
    },
    "root": {"level": "INFO", "handlers": ["app_file"]},
}


_configured = False


def setup_logging() -> tuple[logging.Logger, logging.Logger, logging.Logger]:
    global _configured
    if not _configured:
        logging.config.dictConfig(LOGGING_CONFIG)
        _configured = True
    return (
        logging.getLogger("app"),
        logging.getLogger("services.inference"),
        logging.getLogger("telemetry"),
    )


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    logger.info(event, extra={"extra_data": {"event": event, **fields}})


def log_inference_request(*, request_id: str, prompt: str, model_name: str, strategy: str | None = None) -> None:
    log_event(logging.getLogger("services.inference"), "inference_request", request_id=request_id, prompt=prompt, model_name=model_name, strategy=strategy)


def log_inference_response(*, request_id: str, response_text: str, model_name: str, inference_process_time: float) -> None:
    log_event(logging.getLogger("services.inference"), "inference_response", request_id=request_id, response=response_text, model_name=model_name, latency_seconds=inference_process_time)


def log_inference_telemetry(*, request_id: str, model_used: str, task_type: str | None, inference_process_time: float, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
    tokens_per_second = round(total_tokens / inference_process_time, 4) if inference_process_time > 0 else 0
    log_event(logging.getLogger("telemetry"), "inference_telemetry", request_id=request_id, model_used=model_used, task_type=task_type, latency_seconds=inference_process_time, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens, tokens_per_second=tokens_per_second)


def log_rag_index_access(*, request_id: str, query: str, top_k: int, source: str, retrieved_ids: list[int], latency_seconds: float) -> None:
    log_event(logging.getLogger("rag"), "rag_query", request_id=request_id, query=query, top_k=top_k, source=source, retrieved_ids=retrieved_ids, latency_seconds=latency_seconds)


def log_rag_indexing(*, action: str, path: str, stable_id: str, checksum: str, chunk_count: int, latency_seconds: float) -> None:
    log_event(logging.getLogger("rag"), "rag_indexing", action=action, path=path, stable_id=stable_id, checksum=checksum, chunk_count=chunk_count, latency_seconds=latency_seconds)


def log_db_query(*, operation: str, table: str, filters: dict[str, Any] | None = None, rows: int | None = None, latency_seconds: float | None = None) -> None:
    log_event(logging.getLogger("db"), "db_query", operation=operation, table=table, filters=filters or {}, rows=rows, latency_seconds=latency_seconds)
