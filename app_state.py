"""Zentrale Session-State-Verwaltung der Streamlit-Anwendung."""

from __future__ import annotations

from datetime import datetime

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
    "activity_log": [],
    "technical_log": [],
    "last_traced_search": None,
}


def init_state() -> None:
    """Initialisiert alle globalen App-Zustände genau einmal."""
    for key, value in STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value)


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
