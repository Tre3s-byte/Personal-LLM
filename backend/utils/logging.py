import logging
import logging.config
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s|%(levelname)s|%(name)s|%(message)s"},
        "json": {
            "format": '{"timestamp":"%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "inference_file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": "logs/inference_log.txt",
            "encoding": "utf-8",
        },
        "telemetry_file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "logs/telemetry.json",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "inference": {
            "handlers": ["inference_file"],
            "level": "INFO",
            "propagate": False,
        },
        "telemetry": {
            "handlers": ["telemetry_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
