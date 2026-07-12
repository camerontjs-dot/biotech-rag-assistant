"""Configuration for the controlled-document HTTP transport layer.

The service is bound to a fixed allowlist of corpus bundles at startup. Requests select a
bundle by name; no request ever supplies a filesystem path. This keeps the transport's access
strictly limited to the designated bundle(s).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_NAME = "synthetic"
DEFAULT_CORPUS_PATH = ASSET_ROOT / "examples/synthetic-controlled-docs"


@dataclass(frozen=True)
class ApiConfig:
    """Resolved transport settings. Corpora is the name->path allowlist."""

    corpora: dict[str, Path]
    default_corpus: str
    api_key: str | None = None
    audit_log_path: Path | None = None
    host: str = "127.0.0.1"
    port: int = 8000
    low_score_margin: float = 0.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ApiConfig:
        """Build configuration from environment variables (see docs/api-transport.md)."""
        env = os.environ if env is None else env

        corpora = _parse_corpora(env.get("BIOTECH_RAG_CORPORA"))
        default_corpus = env.get("BIOTECH_RAG_DEFAULT_CORPUS", "").strip() or next(iter(corpora))
        if default_corpus not in corpora:
            raise ValueError(
                f"BIOTECH_RAG_DEFAULT_CORPUS {default_corpus!r} is not in the corpus allowlist"
            )

        api_key = env.get("BIOTECH_RAG_API_KEY", "").strip() or None
        audit_raw = env.get("BIOTECH_RAG_AUDIT_LOG", "").strip()
        audit_log_path = Path(audit_raw) if audit_raw else None
        host = env.get("BIOTECH_RAG_HOST", "").strip() or "127.0.0.1"
        port = int(env.get("BIOTECH_RAG_PORT", "").strip() or "8000")
        low_score_margin = float(env.get("BIOTECH_RAG_LOW_SCORE_MARGIN", "").strip() or "0.0")

        return cls(
            corpora=corpora,
            default_corpus=default_corpus,
            api_key=api_key,
            audit_log_path=audit_log_path,
            host=host,
            port=port,
            low_score_margin=low_score_margin,
        )


def _parse_corpora(raw: str | None) -> dict[str, Path]:
    """Parse a comma-separated ``name=path`` allowlist; default to the bundled synthetic corpus."""
    if not raw or not raw.strip():
        return {DEFAULT_CORPUS_NAME: DEFAULT_CORPUS_PATH}

    corpora: dict[str, Path] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        name, separator, path_str = entry.partition("=")
        name = name.strip()
        path_str = path_str.strip()
        if not separator or not name or not path_str:
            raise ValueError(
                f"invalid BIOTECH_RAG_CORPORA entry (expected name=path): {entry!r}"
            )
        path = Path(path_str)
        if not path.is_absolute():
            path = (ASSET_ROOT / path).resolve()
        corpora[name] = path

    if not corpora:
        return {DEFAULT_CORPUS_NAME: DEFAULT_CORPUS_PATH}
    return corpora
