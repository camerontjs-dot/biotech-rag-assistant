"""Thin demo web UI composed over the pure transport app.

The transport app (`create_app`, ADR-010) stays pure: it only serializes core records.
This module wraps it and adds a single ``GET /`` route that serves a static, self-contained
chat page. The page calls the unchanged ``POST /answer`` contract from the same origin, so it
needs no CORS and cannot bypass the status gate, citation validation, or refusal behavior.
It is a presentation surface in front of the API, not a change to it.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from biotech_rag_assistant.api.app import create_app
from biotech_rag_assistant.api.config import ApiConfig

STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


def create_demo_app(config: ApiConfig | None = None) -> FastAPI:
    """Build the transport app and add the demo chat page at ``GET /``."""
    app = create_app(config)

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(INDEX_HTML, media_type="text/html")

    return app


app = create_demo_app()
