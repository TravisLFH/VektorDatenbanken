"""Kleine, wiederverwendbare Streamlit-Bausteine."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from ui.theme import inject_css


@st.fragment(run_every="1s")
def hot_reload_timer() -> None:
    """Zeigt unten rechts die Zeit seit dem letzten Start oder Code-Reload."""
    last_hot_reload_at = st.session_state.last_hot_reload_at
    elapsed_seconds = max(0, int((datetime.now() - last_hot_reload_at).total_seconds()))
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    st.html(
        f"""
        <style>
            .hot-reload-timer {{
                position: fixed;
                right: 1rem;
                bottom: 1rem;
                z-index: 999999;
                padding: 0.35rem 0.65rem;
                border: 1px solid rgba(15, 118, 110, 0.25);
                border-radius: 999px;
                background: rgba(248, 250, 252, 0.96);
                box-shadow: 0 2px 10px rgba(15, 23, 42, 0.12);
                color: #24313a;
                font: 12px/1.3 sans-serif;
                pointer-events: none;
            }}
        </style>
        <div class="hot-reload-timer">
            Hot Reload: {hours:02d}:{minutes:02d}:{seconds:02d}
        </div>
        """
    )


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


def metadata_chips(entry: dict[str, Any]) -> str:
    """Rendert Kategorien als kompakte, graue Karten-Metadaten."""
    values = []
    category = entry.get("category")
    if isinstance(category, list):
        values.extend(str(value) for value in category)
    elif category:
        values.append(str(category))
    chips = "".join(f'<span class="metadata-chip">{escape(value)}</span>' for value in values)
    return f'<div class="metadata-chips">{chips}</div>' if chips else ""


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


def technical_console() -> None:
    """Zeigt die letzten technischen Datenbank-Interaktionen als Trace an."""
    section("Technische Konsole", "Letzte Inputs und Outputs der Datenbankaktionen.")
    entries = st.session_state.get("technical_log", [])
    with st.container(border=True):
        if not entries:
            st.caption("Noch keine Datenbankaktion ausgeführt.")
        else:
            for index, entry in enumerate(reversed(entries)):
                st.caption(
                    f"{entry['timestamp']} · {entry['user']} · {entry['operation']}"
                )
                st.code(
                    f"INPUT\n{entry['input']}\n\nOUTPUT\n{entry['output']}",
                    language="text",
                )
                if index < len(entries) - 1:
                    st.divider()
        if st.button("Konsole leeren", icon=":material/clear_all:", width="content"):
            st.session_state.technical_log = []
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
            st.markdown(metadata_chips(entry), unsafe_allow_html=True)
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