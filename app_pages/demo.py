"""Interaktive Demo mit Einträgen, Suche, Vektorraum und Datenverwaltung."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA

from app_state import mark_data_changed, record_activity
from data_access import load_user_objects, run_user_search
from demo_data import DEMO_SUCHANFRAGEN
from errors import EntryNotFoundError, ValidationError
from ui.components import empty_state, entry_row, page_header, section
from ui.theme import apply_chart_style

logger = logging.getLogger(__name__)
db = st.session_state.db
active_user = st.session_state.active_user


def _reset_search() -> None:
    st.session_state.search_nonce += 1
    st.session_state.last_search_query = ""
    st.session_state.search_query_input = ""
    st.session_state.search_suggestion = ""


@st.dialog("Eintrag löschen")
def _delete_dialog(entry: dict) -> None:
    st.markdown(f"**{entry.get('name', 'Ohne Namen')}**")
    st.caption(entry.get("description", "Keine Beschreibung"))
    st.warning("Diese Aktion kann nicht rückgängig gemacht werden.")
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Endgültig löschen", type="primary", icon=":material/delete_forever:", width="stretch"):
        try:
            db.delete_data(entry["id"], active_user)
            record_activity(
                "Löschen",
                f"Eintrag '{entry.get('name', 'Ohne Namen')}' wurde aus der Datenbank gelöscht.",
                active_user,
            )
            mark_data_changed()
            st.session_state.pending_delete_id = None
            st.toast("Eintrag gelöscht.")
            st.rerun()
        except EntryNotFoundError:
            st.error("Der Eintrag existiert nicht mehr oder gehört nicht zum aktiven Nutzer.")
        except Exception:
            logger.exception("Eintrag konnte nicht gelöscht werden.")
            st.error("Der Eintrag konnte nicht gelöscht werden. Prüfe die Qdrant-Verbindung.")
    if cancel_col.button("Abbrechen", width="stretch"):
        st.session_state.pending_delete_id = None
        st.rerun()


def _render_entry_form(objects_by_id: dict[str, dict]) -> None:
    editing_id = st.session_state.editing_point_id
    editing_entry = objects_by_id.get(editing_id) if editing_id else None
    should_scroll = st.session_state.pop("scroll_to_entry_form", False)
    st.markdown('<div id="entry-form-anchor"></div>', unsafe_allow_html=True)
    if should_scroll:
        st.html(
            """
            <script>
            requestAnimationFrame(() => {
                document.getElementById("entry-form-anchor")?.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            });
            </script>
            """,
            unsafe_allow_javascript=True,
        )
    with st.container(border=True):
        if editing_entry:
            st.markdown(
                f'<h3>Du bearbeitest: <strong>{editing_entry["name"]}</strong> '
                f'<span class="technical-label">&middot; UUID: {editing_entry["id"]}</span></h3>',
                unsafe_allow_html=True,
            )
        else:
            section("Neuen Eintrag anlegen", "Name und Beschreibung werden gemeinsam eingebettet, damit Qdrant nach Bedeutung suchen kann.")
        with st.form(f"entry_form_{st.session_state.form_nonce}", clear_on_submit=False):
            name = st.text_input("Name", value=editing_entry.get("name", "") if editing_entry else "", max_chars=db.config.max_name_length, placeholder="z. B. Mars", help="Ein kurzer, gut erkennbarer Name des Eintrags.")
            description = st.text_area("Beschreibung", value=editing_entry.get("description", "") if editing_entry else "", max_chars=db.config.max_description_length, placeholder="z. B. Ein roter Planet mit einer dünnen Atmosphäre ...", help="Die Beschreibung wird für die semantische Suche in ein 384-dimensionales Embedding umgewandelt.")
            if editing_entry:
                cancel_col, save_col = st.columns([3, 7])
                cancel_clicked = cancel_col.form_submit_button("Bearbeitung abbrechen", icon=":material/close:", width="stretch")
                submitted = save_col.form_submit_button("Änderung speichern", type="primary", icon=":material/save:", width="stretch")
            else:
                cancel_clicked = False
                submitted = st.form_submit_button("Eintrag speichern", type="primary", icon=":material/save:", width="stretch")
        if cancel_clicked:
            st.session_state.editing_point_id = None
            st.session_state.form_nonce += 1
            st.rerun()
        if not submitted:
            return
        if not name.strip() or not description.strip():
            st.warning("Bitte Name und Beschreibung ausfüllen.")
            return
        try:
            with st.spinner("Embedding wird erzeugt und gespeichert ..."):
                if editing_entry:
                    db.update_data(editing_id, name, description, active_user)
                    record_activity("Aktualisieren", f"Eintrag '{name}' wurde aktualisiert.", active_user)
                    message = f"'{name}' wurde aktualisiert."
                else:
                    point_id = db.insert_data(name, description, active_user)
                    record_activity(
                        "Einfügen",
                        f"Eintrag '{name}' wurde hinzugefügt (UUID: {point_id}).",
                        active_user,
                    )
                    message = f"'{name}' wurde eingefügt."
            mark_data_changed()
            st.toast(message)
            st.rerun()
        except (ValidationError, EntryNotFoundError) as exc:
            st.warning(str(exc))
        except Exception:
            logger.exception("Eintrag konnte nicht gespeichert werden.")
            st.error("Der Eintrag konnte nicht gespeichert werden. Prüfe die Qdrant-Verbindung.")


@st.fragment
def _render_entries(objects: list[dict]) -> None:
    section("Deine Einträge", "Aktionen bleiben direkt am jeweiligen Eintrag und verwenden dessen UUID.")
    count_col, filter_col = st.columns([1, 3])
    count_col.metric("Einträge", len(objects))
    filter_value = filter_col.text_input("Einträge filtern", key="entry_filter", placeholder="Nach Name oder Beschreibung filtern", label_visibility="collapsed")
    search = filter_value.casefold().strip()
    filtered = [entry for entry in objects if not search or search in entry.get("name", "").casefold() or search in entry.get("description", "").casefold()]
    if not filtered:
        empty_state("Keine passenden Einträge gefunden.", "Leere den Filter oder lege einen neuen Eintrag an.")
        return
    for entry in filtered:
        edit_clicked, delete_clicked = entry_row(entry, editing=entry["id"] == st.session_state.editing_point_id)
        if edit_clicked:
            st.session_state.editing_point_id = entry["id"]
            st.session_state.scroll_to_entry_form = True
            st.session_state.form_nonce += 1
            st.rerun()
        if delete_clicked:
            st.session_state.pending_delete_id = entry["id"]
            st.rerun()
@st.fragment
def _render_search(objects: list[dict]) -> None:
    section("Semantische Suche", "Formuliere eine Bedeutung statt eines exakten Schlüsselworts.")
    with st.expander("Beispielfragen anzeigen"):
        suggestion = st.selectbox(
            "Demo-Frage auswählen",
            DEMO_SUCHANFRAGEN,
            index=None,
            key="search_suggestion",
            placeholder="Eine Beispielanfrage auswählen ...",
        )
        if st.button("Frage übernehmen", icon=":material/input:", disabled=suggestion is None):
            st.session_state.search_query_input = suggestion
            st.rerun()
    with st.form(f"search_form_{st.session_state.search_nonce}"):
        query = st.text_input("Suchanfrage", key="search_query_input", placeholder="z. B. Person, die Mathematik unterrichtet", label_visibility="collapsed")
        search_col, reset_col = st.columns([3, 1])
        submitted = search_col.form_submit_button("Suchen", type="primary", icon=":material/search:", width="stretch")
        reset = reset_col.form_submit_button(
            "Zurücksetzen",
            icon=":material/refresh:",
            width="stretch",
            on_click=_reset_search,
        )
    if reset:
        st.rerun()
    if submitted:
        if not query.strip():
            st.warning("Bitte eine Suchanfrage eingeben.")
        else:
            st.session_state.last_search_query = query.strip()
            record_activity("Suche", f"Semantische Suche nach '{query.strip()}' gestartet.", active_user)
            st.rerun()
    query = st.session_state.get("last_search_query", "")
    if not query:
        st.info("Gib eine Anfrage ein, um semantisch ähnliche Einträge zu finden.", icon=":material/search:")
        return
    with st.spinner("Ähnliche Einträge werden gesucht ..."):
        results = run_user_search(db, query_text=query, user_id=active_user, limit=min(max(len(objects), 1), db.config.max_search_limit), data_version=st.session_state.data_version, include_vectors=False)
    if not results:
        empty_state("Keine Treffer für diese Anfrage.", "Versuche eine allgemeinere Beschreibung.")
        return
    for index, result in enumerate(results, start=1):
        with st.container(border=True):
            top_col, score_col = st.columns([4, 1])
            top_col.markdown(f"**{index}. {result['name']}**")
            top_col.caption(result["description"])
            score_col.metric("Ähnlichkeit", f"{result['score']:.0%}")


@st.fragment
def _render_vector_space(objects: list[dict]) -> None:
    section("Vektorraum", "Die PCA projiziert 384 Dimensionen für die Darstellung auf zwei Achsen.")
    if len(objects) < 3:
        st.info("Für die Darstellung werden mindestens 3 Einträge benötigt.", icon=":material/scatter_plot:")
        return
    if not st.checkbox("PCA-Visualisierung laden", key="show_pca"):
        st.info("Die Berechnung startet erst nach deiner Anforderung.")
        return
    with st.spinner("PCA-Projektion wird berechnet ..."):
        vector_objects = load_user_objects(db, active_user, st.session_state.data_version, include_vectors=True)
        vectors = np.array([entry["vector"] for entry in vector_objects])
        coordinates = PCA(n_components=2).fit_transform(vectors)
    plot_data = pd.DataFrame({"x": coordinates[:, 0], "y": coordinates[:, 1], "Name": [entry["name"] for entry in vector_objects], "Beschreibung": [entry["description"] for entry in vector_objects]})
    fig = px.scatter(plot_data, x="x", y="y", text="Name", hover_data={"Beschreibung": True, "x": False, "y": False})
    fig.update_traces(textposition="top center", marker={"size": 12, "color": "#0f766e"})
    fig.update_layout(title=f"2D-Projektion der Einträge für {active_user}", xaxis_title="PCA-Achse 1", yaxis_title="PCA-Achse 2")
    st.plotly_chart(apply_chart_style(fig), width="stretch")
    st.caption("Nahe Punkte sind im ursprünglichen 384-dimensionalen Raum semantisch ähnlicher. Die Grafik ist eine Projektion und kein vollständiger Vektorvergleich.")
    selected_id = st.selectbox("Technische Vektordetails anzeigen", [entry["id"] for entry in vector_objects], format_func=lambda point_id: next(entry["name"] for entry in vector_objects if entry["id"] == point_id))
    selected = next(entry for entry in vector_objects if entry["id"] == selected_id)
    vector = np.array(selected["vector"])
    st.caption(f"{len(vector)} Dimensionen · erste zehn Werte")
    st.dataframe(pd.DataFrame({"Dimension": range(1, 11), "Wert": vector[:10]}), hide_index=True, width="stretch")


@st.fragment
def _render_data_management() -> None:
    section("Datenverwaltung", "Demo-Daten und technische Wartungsaktionen für den aktiven Nutzer.")
    with st.container(border=True):
        if st.button("Demodaten hinzufügen", icon=":material/auto_awesome:", width="stretch"):
            try:
                with st.spinner("Demodaten werden erzeugt ..."):
                    count = db.seed_demo_data(active_user)
                record_activity("Demodaten", f"{count} Beispielwerte wurden hinzugefügt.", active_user)
                mark_data_changed()
                st.toast(f"{count} Demodaten für {active_user} eingefügt.")
                st.rerun()
            except Exception:
                logger.exception("Demodaten konnten nicht angelegt werden.")
                st.error("Die Demodaten konnten nicht angelegt werden.")
        if st.button("Suchvektoren neu erzeugen", icon=":material/sync:", width="stretch"):
            try:
                with st.spinner("Suchvektoren werden neu erzeugt ..."):
                    count = db.reindex_user_data(active_user)
                record_activity("Re-Embedding", f"{count} Suchvektoren wurden neu erzeugt.", active_user)
                mark_data_changed()
                st.toast(f"{count} Suchvektoren aktualisiert.")
                st.rerun()
            except Exception:
                logger.exception("Re-Embedding konnte nicht ausgeführt werden.")
                st.error("Die Suchvektoren konnten nicht neu erzeugt werden.")
    with st.container(border=True):
        st.subheader("Gefahrenbereich")
        st.warning("Löschaktionen können nicht rückgängig gemacht werden.")
        if st.button("Daten des aktuellen Nutzers löschen", icon=":material/person_remove:", width="stretch"):
            st.session_state.confirm_delete_user = True
        if st.session_state.confirm_delete_user:
            st.write(f"Alle {db.count_for_user(active_user)} Einträge von {active_user} löschen?")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Nutzerdaten endgültig löschen", type="primary", key="confirm_user_delete", width="stretch"):
                count = db.count_for_user(active_user)
                db.delete_user_data(active_user)
                record_activity("Nutzerlöschung", f"{count} Einträge wurden für diesen Nutzer gelöscht.", active_user)
                st.session_state.confirm_delete_user = False
                mark_data_changed()
                st.toast("Die Nutzerdaten wurden gelöscht.")
                st.rerun()
            if cancel_col.button("Abbrechen", key="cancel_user_delete", width="stretch"):
                st.session_state.confirm_delete_user = False
                st.rerun()
        if st.button("ALLE Daten löschen", icon=":material/delete_forever:", width="stretch"):
            st.session_state.confirm_delete_all = True
        if st.session_state.confirm_delete_all:
            st.error("Diese Aktion löscht die Daten aller Nutzer.")
            confirmation = st.text_input("Zur Bestätigung LÖSCHEN eingeben", key="global_delete_confirmation")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Alle Daten endgültig löschen", type="primary", key="confirm_all_delete", width="stretch"):
                if confirmation == "LÖSCHEN":
                    count = db.count_all()
                    db.delete_all_data()
                    record_activity("Gesamtlöschung", f"{count} Einträge aller Nutzer wurden gelöscht.", active_user)
                    st.session_state.confirm_delete_all = False
                    mark_data_changed()
                    st.toast("Alle Daten wurden gelöscht.")
                    st.rerun()
                else:
                    st.warning("Die Bestätigung stimmt nicht überein.")
            if cancel_col.button("Abbrechen", key="cancel_all_delete", width="stretch"):
                st.session_state.confirm_delete_all = False
                st.rerun()


page_header("Vektordatenbank-Demo", "Einträge verwalten, Bedeutungen suchen und Embeddings sichtbar machen.")
user_objects = load_user_objects(db, active_user, st.session_state.data_version, include_vectors=False)
objects_by_id = {entry["id"]: entry for entry in user_objects}
if st.session_state.pending_delete_id:
    pending_entry = objects_by_id.get(st.session_state.pending_delete_id)
    if pending_entry:
        _delete_dialog(pending_entry)
    else:
        st.session_state.pending_delete_id = None

entries_tab, search_tab, vector_tab, management_tab = st.tabs(["Einträge", "Suche", "Vektorraum", "Datenverwaltung"])
with entries_tab:
    _render_entry_form(objects_by_id)
    st.divider()
    if user_objects:
        _render_entries(user_objects)
    else:
        empty_state("Noch keine Einträge.", "Lege oben deinen ersten Eintrag an oder erzeuge Demo-Daten in der Datenverwaltung.")
with search_tab:
    _render_search(user_objects)
with vector_tab:
    _render_vector_space(user_objects)
with management_tab:
    _render_data_management()
