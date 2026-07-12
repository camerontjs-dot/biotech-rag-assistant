"""HTTP transport package for the controlled-document retrieval pilot.

Exposes the same core functions the CLI calls over FastAPI, serializing the same
``to_cli_record()`` output so API JSON matches the CLI. No core logic lives here.
"""

from __future__ import annotations

from biotech_rag_assistant.api.app import app, create_app
from biotech_rag_assistant.api.config import ApiConfig

__all__ = ["ApiConfig", "app", "create_app"]
