import json
import logging
import logging.config
from typing import Any
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JsonFormatter(logging.Formatter):
    def _sanitize(self, obj):
        if obj is ...:
            return None
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        return obj

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        # If structured telemetry
        if hasattr(record, "event_payload"):
            payload.update(record.event_payload)
        else:
            payload["message"] = record.getMessage()

        safe_payload = self._sanitize(payload)

        return json.dumps(safe_payload, ensure_ascii=False)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s|%(levelname)s|%(name)s|%(message)s",
        },
        "json": {
            "()": JsonFormatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(LOG_DIR / "app.log"),
            "encoding": "utf-8",
            "maxBytes": 5_000_000,
            "backupCount": 3,
        },
        "inference_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": str(LOG_DIR / "inference.log"),
            "encoding": "utf-8",
            "maxBytes": 5_000_000,
            "backupCount": 3,
        },
        "telemetry_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": str(LOG_DIR / "telemetry.jsonl"),
            "encoding": "utf-8",
            "maxBytes": 5_000_000,
            "backupCount": 3,
        },
    },
    "loggers": {
        "services.inference": {
            "handlers": ["inference_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "telemetry": {
            "handlers": ["telemetry_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "app_file"],
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)


inference_logger = logging.getLogger("services.inference")
telemetry_logger = logging.getLogger("telemetry")


def _sanitize(obj: Any):
    if obj is ...:
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def log_inference_started(model_name: str, strategy: str | None = None) -> None:
    inference_logger.info(
        f"Starting routed inference | model={model_name} strategy={strategy}"
    )


def log_inference_completed(model_name: str, latency_seconds: float) -> None:
    inference_logger.info(
        f"Completed routed inference | model={model_name} latency={latency_seconds:.2f}s"
    )


def log_inference_telemetry(
    *,
    model: str,
    task_type: str | None,
    strategy: str | None,
    latency_seconds: float,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    models_used: list[str] | None = None,
    chunk_info: dict[str, Any] | None = None,
) -> None:
    tokens_per_second = (
        round(total_tokens / latency_seconds, 4)
        if latency_seconds > 0 and total_tokens > 0
        else None
    )

    payload = {
        "event": "inference_complete",
        "model": model,
        "models_used": models_used or [model],
        "task_type": task_type,
        "strategy": strategy,
        "latency_seconds": round(latency_seconds, 4),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_per_second": tokens_per_second,
        "chunk_info": chunk_info
        or {
            "chunk_count": 1,
            "chunk_size": None,
            "chunk_strategy": "none",
        },
    }

    telemetry_logger.info("", extra={"event_payload": _sanitize(payload)})
