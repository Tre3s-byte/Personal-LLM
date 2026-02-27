import json
import logging
import logging.config
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


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
        "inference": {
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
