"""Structured JSON logging configuration and inference telemetry emitters."""

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

        # If response exists, preserve formatting cleanly
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
