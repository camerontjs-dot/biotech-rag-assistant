"""Structured per-request audit logging for the transport layer.

Every non-health request emits one audit record so retrieval and answer context stays
traceable. Records go to Python logging and, when an audit-log path is configured, are
appended as JSON lines.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("biotech_rag_assistant.api.audit")


def emit_audit_record(record: dict[str, Any], audit_log_path: Path | None) -> None:
    """Emit one audit record to the logger and, if configured, an append-only JSONL file."""
    line = json.dumps(record, sort_keys=True, default=str)
    logger.info("audit %s", line)
    if audit_log_path is not None:
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
