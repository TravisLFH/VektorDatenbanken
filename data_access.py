"""Gecachte, nutzergebundene Leseoperationen für die Streamlit-Oberfläche."""

from __future__ import annotations

from typing import Any

import streamlit as st


@st.cache_data(max_entries=100)
def load_user_objects(
    _manager: Any, user_id: str, data_version: int, include_vectors: bool = False
) -> list[dict]:
    """Lädt den Nutzerbestand; Version und Nutzer verhindern stale/leaky Cache-Treffer."""
    del data_version
    return _manager.get_all_for_user(user_id, include_vectors=include_vectors)


@st.cache_data(max_entries=200)
def run_user_search(
    _manager: Any,
    query_text: str,
    user_id: str,
    limit: int,
    data_version: int,
    category: str | None = None,
    include_vectors: bool = False,
) -> list[dict]:
    """Cached eine Suche ausschließlich mit Nutzer- und Datenversionsschlüssel."""
    del data_version
    return _manager.search_data(
        query_text=query_text,
        user_id=user_id,
        limit=limit,
        category=category,
        include_vectors=include_vectors,
    )
