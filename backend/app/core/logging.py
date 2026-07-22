import json
import logging
import sys
from datetime import UTC, datetime
from logging.config import dictConfig
from typing import Any


RESERVED_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {
    "asctime",
    "message",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in RESERVED_LOG_RECORD_FIELDS
        }
        if context:
            payload["context"] = context

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "json",
                },
            },
            "root": {
                "handlers": ["default"],
                "level": log_level.upper(),
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": log_level.upper(),
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": log_level.upper(),
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": log_level.upper(),
                    "propagate": False,
                },
            },
        }
    )
