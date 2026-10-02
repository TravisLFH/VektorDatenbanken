"""Kleine, wiederverwendbare Streamlit-Bausteine."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.theme import inject_css


def page_header(title: str, subtitle: str) -> None:
    inject_css()
    st.markdown(
        f'<div class="app-page-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Aktiver Nutzer: {st.session_state.get('active_user', 'Nutzer A')}")


def section(title: str, description: str | None = None) -> None:
    st.subheader(title)
    if description:
        st.caption(description)


def empty_state(message: str, hint: str | None = None) -> None:
    st.info(message, icon=":material/inbox:")
    if hint:
        st.caption(hint)


def activity_log() -> None:
    """Zeigt die letzten fachlich relevanten Aktionen der aktuellen Sitzung."""
    section("Aktivitätsprotokoll", "Nachvollziehbare Ausgaben für die praktische Vorführung.")
    entries = st.session_state.get("activity_log", [])
    with st.container(border=True):
        if entries:
            st.text_area(
                "Protokoll",
                value="\n".join(reversed(entries)),
                height=170,
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            st.caption("Noch keine Aktionen ausgeführt. Die nächsten Datenbankaktionen erscheinen hier.")
        if st.button("Protokoll leeren", icon=":material/clear_all:", width="content"):
            st.session_state.activity_log = []
            st.rerun()


def entry_row(entry: dict[str, Any], editing: bool = False) -> tuple[bool, bool]:
    """Rendert eine Eintragszeile und gibt Bearbeiten-/Löschen-Klicks zurück."""
    with st.container(border=True):
        if editing:
            st.caption("Wird bearbeitet")
        info_col, edit_col, delete_col = st.columns([6, 1, 1], vertical_alignment="center")
        with info_col:
            st.markdown(
                f'<strong>{entry.get("name", "Ohne Namen")}</strong> '
                f'<span class="technical-label">&middot; UUID: {entry["id"]}</span>',
                unsafe_allow_html=True,
            )
            st.caption(entry.get("description", "Keine Beschreibung"))
        with edit_col:
            edit_clicked = st.button(
                "Bearbeiten",
                key=f"edit_{entry['id']}",
                icon=":material/edit:",
                type="secondary",
                width="stretch",
                help="Diesen Eintrag per UUID in das Formular laden.",
            )
        with delete_col:
            delete_clicked = st.button(
                "Löschen",
                key=f"delete_{entry['id']}",
                icon=":material/delete:",
                type="secondary",
                width="stretch",
                help="Diesen Eintrag zur bestätigten Löschung auswählen.",
            )
    return edit_clicked, delete_clicked