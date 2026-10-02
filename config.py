"""Zentrale Konfiguration der lokalen Vektordatenbank-Demo."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_USERS = ("Nutzer A", "Nutzer B")


@dataclass(frozen=True)
class AppConfig:
    """Konfiguration aus Umgebungsvariablen mit robusten Demo-Defaults."""

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_timeout: float = 5.0
    collection_name: str = "space_objects"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384
    max_name_length: int = 120
    max_description_length: int = 2000
    default_search_limit: int = 5
    max_search_limit: int = 50

    @classmethod
    def from_env(cls) -> AppConfig:
        """Liest die Konfiguration und verwirft ungültige Zahlenwerte."""
        return cls(
            qdrant_host=_env_text("QDRANT_HOST", cls.qdrant_host),
            qdrant_port=_env_int("QDRANT_PORT", cls.qdrant_port, minimum=1, maximum=65535),
            qdrant_api_key=os.getenv("QDRANT_API_KEY") or None,
            qdrant_timeout=_env_float("QDRANT_TIMEOUT", cls.qdrant_timeout, minimum=0.1),
            collection_name=_env_text("QDRANT_COLLECTION", cls.collection_name),
            embedding_model=_env_text("EMBEDDING_MODEL", cls.embedding_model),
            embedding_dimension=_env_int("EMBEDDING_DIMENSION", cls.embedding_dimension, minimum=1),
            max_name_length=_env_int("MAX_NAME_LENGTH", cls.max_name_length, minimum=1),
            max_description_length=_env_int(
                "MAX_DESCRIPTION_LENGTH", cls.max_description_length, minimum=1
            ),
            default_search_limit=_env_int("DEFAULT_SEARCH_LIMIT", cls.default_search_limit, minimum=1),
            max_search_limit=_env_int("MAX_SEARCH_LIMIT", cls.max_search_limit, minimum=1),
        )


def _env_text(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


def _env_int(name: str, default: int, minimum: int, maximum: int | None = None) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    if value < minimum or (maximum is not None and value > maximum):
        return default
    return value


def _env_float(name: str, default: float, minimum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value >= minimum else default


CONFIG = AppConfig.from_env()
USERS = DEFAULT_USERS
