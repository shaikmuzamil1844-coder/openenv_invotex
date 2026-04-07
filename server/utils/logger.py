"""Structured logging with trace-ID context variable."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class TraceFilter(logging.Filter):
    """Injects trace_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        return True


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(TraceFilter())
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s trace=%(trace_id)s | %(message)s"
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
