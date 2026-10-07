"""Zentrale Session-State-Verwaltung der Streamlit-Anwendung."""

from __future__ import annotations

from datetime import datetime

import os
from datetime import datetime
from pathlib import Path

import streamlit as st


STATE_DEFAULTS = {
    "active_user": "Nutzer A",
    "active_user_previous": "Nutzer A",
    "editing_point_id": None,
    "scroll_to_entry_form": False,
    "pending_delete_id": None,
    "pending_delete_name": None,
    "confirm_delete_user": False,
    "confirm_delete_all": False,
    "data_version": 0,
    "form_nonce": 0,
    "search_nonce": 0,
    "entry_filter": "",
    "active_tab": "Einträge",
    "global_delete_confirmation": "",
    "last_search_query": "",
    "search_query_input": "",
    "search_suggestion": "",
    "search_category_filter": [],
    "show_pca": False,
    "show_search_projection": False,
    "show_stored_vectors": False,
    "activity_log": [],
    "technical_log": [],
    "last_traced_search": None,
    "python_source_signature": None,
    "last_hot_reload_at": None,
    "last_search_at": None,
}


def init_state() -> None:
    """Initialisiert alle globalen App-Zustände genau einmal."""
    for key, value in STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value)
    update_hot_reload_state()


def update_hot_reload_state() -> None:
    """Erkennt Quellcodeänderungen ohne normale Widget-Reruns als Reload zu zählen."""
    project_root = Path(__file__).resolve().parent
    excluded_directories = {".git", ".pytest_cache", ".venv", "__pycache__", "qdrant_storage"}
    signature = []
    for directory, subdirectories, filenames in os.walk(project_root):
        subdirectories[:] = [
            name for name in subdirectories if name not in excluded_directories
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                source_path = Path(directory, filename)
                metadata = source_path.stat()
                signature.append(
                    (
                        str(source_path.relative_to(project_root)),
                        metadata.st_mtime_ns,
                        metadata.st_size,
                    )
                )

    current_signature = tuple(sorted(signature))
    previous_signature = st.session_state.python_source_signature
    if previous_signature != current_signature:
        if previous_signature is not None or st.session_state.last_hot_reload_at is None:
            st.session_state.last_hot_reload_at = datetime.now()
        st.session_state.python_source_signature = current_signature


def reset_user_state() -> None:
    """Setzt nutzerabhängige Auswahl-, Such- und Bearbeitungszustände zurück."""
    st.session_state.editing_point_id = None
    st.session_state.pending_delete_id = None
    st.session_state.pending_delete_name = None
    st.session_state.form_nonce += 1
    st.session_state.search_nonce += 1
    st.session_state.entry_filter = ""
    st.session_state.active_tab = "Einträge"
    st.session_state.last_search_query = ""
    st.session_state.search_query_input = ""
    st.session_state.search_suggestion = ""
    st.session_state.search_category_filter = []
    st.session_state.show_pca = False
    st.session_state.show_search_projection = False
    st.session_state.show_stored_vectors = False
    st.session_state.data_version += 1


def mark_data_changed() -> None:
    """Invalidiert nutzerbezogene Lesecaches über eine monotone Versionsnummer."""
    st.session_state.data_version += 1
    st.session_state.editing_point_id = None
    st.session_state.pending_delete_id = None
    st.session_state.pending_delete_name = None
    st.session_state.form_nonce += 1
    st.session_state.last_search_query = ""


def record_activity(action: str, message: str, user_id: str | None = None) -> None:
    """Speichert ein kurzes, für die Demo relevantes Ereignis im Session-State."""
    user_label = user_id or st.session_state.get("active_user", "Unbekannter Nutzer")
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"{timestamp} | {user_label} | {action}: {message}"
    activity_log = st.session_state.setdefault("activity_log", [])
    activity_log.append(entry)
    del activity_log[:-25]


def record_technical_event(
    operation: str,
    input_data: str,
    output_data: str,
    user_id: str | None = None,
) -> None:
    """Speichert einen kompakten Input-/Output-Trace für die Demo-Sidebar."""
    user_label = user_id or st.session_state.get("active_user", "Unbekannter Nutzer")
    technical_log = st.session_state.setdefault("technical_log", [])
    technical_log.append(
        {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user": user_label,
            "operation": operation,
            "input": input_data,
            "output": output_data,
        }
    )
    del technical_log[:-12]
