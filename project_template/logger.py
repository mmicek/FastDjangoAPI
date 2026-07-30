import logging
from logging import basicConfig
from logging.config import dictConfig

from project_template.config import Env, settings

JSON_LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["json"],
        "level": "INFO",
    },
    "loggers": {
        # Prevent uvicorn from using its own text handlers.
        "uvicorn": {"handlers": ["json"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["json"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["json"], "level": "INFO", "propagate": False},
    },
}


def configure_logging() -> None:
    if settings.ENV == Env.LOCAL:
        basicConfig(level=logging.INFO)
    else:
        dictConfig(JSON_LOGGING_CONFIG)
