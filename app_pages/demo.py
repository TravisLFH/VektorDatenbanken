"""Interaktive Demo mit Einträgen, Suche, Vektorraum und Datenverwaltung."""
from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA

from app_state import mark_data_changed, record_activity, record_technical_event
from data_access import load_user_objects, run_user_search
from demo_data import DEMO_SUCHANFRAGEN
from errors import EntryNotFoundError, ValidationError
from ui.components import empty_state, entry_row, metadata_chips, page_header, section
from ui.theme import apply_chart_style

logger = logging.getLogger(__name__)
db = st.session_state.db
active_user = st.session_state.active_user
CATEGORY_OPTIONS = (
    "Sonstiges",
    "Job",
    "Person",
    "Gemüse",
    "Obst",
    "Gegenstand",
    "Fahrzeug",
    "Tier",
    "Dokument",
    "Ort",
)


def _reset_search() -> None:
    st.session_state.search_nonce += 1
    st.session_state.last_search_query = ""
    st.session_state.search_query_input = ""
    st.session_state.search_suggestion = ""
    st.session_state.search_category_filter = []


@st.dialog("Eintrag löschen")
def _delete_dialog(entry: dict) -> None:
    st.markdown(f"**{entry.get('name', 'Ohne Namen')}**")
    st.caption(entry.get("description", "Keine Beschreibung"))
    st.warning("Diese Aktion kann nicht rückgängig gemacht werden.")
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button("Endgültig löschen", type="primary", icon=":material/delete_forever:", width="stretch"):
        try:
            db.delete_data(entry["id"], active_user)
            record_technical_event(
                "Qdrant DELETE",
                f"collection=space_objects\npoint_id={entry['id']}\nuser_id={active_user}",
                f"deleted=true\nname={entry.get('name', 'Ohne Namen')}",
                active_user,
            )
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
            description = st.text_area("Beschreibung", value=editing_entry.get("description", "") if editing_entry else "", max_chars=db.config.max_description_length, placeholder="z. B. Ein roter Planet mit einer dünnen Atmosphäre ...", help=f"Die Beschreibung wird für die semantische Suche in ein {db.config.embedding_dimension}-dimensionales Embedding umgewandelt.")
            current_categories = editing_entry.get("category", ["Sonstiges"]) if editing_entry else ["Sonstiges"]
            if isinstance(current_categories, str):
                current_categories = [current_categories]
            categories = st.multiselect(
                "Kategorien",
                CATEGORY_OPTIONS,
                default=[category for category in current_categories if category in CATEGORY_OPTIONS],
                help="Kategorien bleiben als Payload getrennt vom Embedding und können serverseitig gefiltert werden.",
            )
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
        if not categories:
            st.warning("Bitte mindestens eine Kategorie auswählen.")
            return
        try:
            metadata = {"category": categories}
            with st.spinner("Embedding wird erzeugt und gespeichert ..."):
                if editing_entry:
                    db.update_data(editing_id, name, description, active_user, metadata=metadata)
                    record_technical_event(
                        "Qdrant UPSERT",
                        f"point_id={editing_id}\nname={name}\ndescription={description}",
                        f"updated=true\nembedding=recomputed\nvector_size={db.config.embedding_dimension}",
                        active_user,
                    )
                    record_activity("Aktualisieren", f"Eintrag '{name}' wurde aktualisiert.", active_user)
                    message = f"'{name}' wurde aktualisiert."
                else:
                    point_id = db.insert_data(name, description, active_user, metadata=metadata)
                    record_technical_event(
                        "Qdrant UPSERT",
                        f"name={name}\ndescription={description}\nuser_id={active_user}",
                        f"inserted=true\npoint_id={point_id}\nvector_size={db.config.embedding_dimension}",
                        active_user,
                    )
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
    filtered = [
        entry
        for entry in objects
        if not search
        or search in entry.get("name", "").casefold()
        or search in entry.get("description", "").casefold()
        or search in str(entry.get("category", "")).casefold()
    ]
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
    category_filter = st.multiselect(
        "Kategorien einschränken",
        CATEGORY_OPTIONS,
        key="search_category_filter",
        help="Die Kategorie wird zusätzlich zur semantischen Ähnlichkeit direkt in Qdrant gefiltert.",
    )
    selected_category = tuple(category_filter) if category_filter else None
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
        results = run_user_search(db, query_text=query, user_id=active_user, limit=min(max(len(objects), 1), db.config.max_search_limit), data_version=st.session_state.data_version, category=selected_category, include_vectors=False)
    search_key = (active_user, query, selected_category, st.session_state.data_version)
    if st.session_state.get("last_traced_search") != search_key:
        result_lines = [
            f"{result['name']} (score={result['score']:.3f})"
            for result in results[:5]
        ]
        record_technical_event(
            "Qdrant QUERY",
            f"query={query}\nuser_id={active_user}\nlimit={len(results)}\ndistance=COSINE",
            f"hits={len(results)}\n" + ("\n".join(result_lines) if result_lines else "no_results"),
            active_user,
        )
        st.session_state.last_traced_search = search_key
    if not results:
        empty_state("Keine Treffer für diese Anfrage.", "Versuche eine allgemeinere Beschreibung.")
        return
    for index, result in enumerate(results, start=1):
        with st.container(border=True):
            top_col, score_col = st.columns([4, 1])
            top_col.markdown(f"**{index}. {result['name']}**")
            top_col.caption(result["description"])
            top_col.markdown(metadata_chips(result), unsafe_allow_html=True)
            score_col.metric("Ähnlichkeit", f"{result['score']:.0%}")


@st.fragment
def _render_stored_vectors(objects: list[dict]) -> None:
    section(
        "Gespeicherte Vektordaten",
        "Die Karten entsprechen der Eintragsübersicht. Lade bei Bedarf die vollständige "
        "Qdrant-Punktstruktur mit Payload und allen Vektordimensionen.",
    )
    if not objects:
        empty_state("Noch keine Einträge für diesen Nutzer vorhanden.")
        return

    show_vectors = st.checkbox(
        "Vollständige Vektoren und gespeicherte Daten anzeigen",
        key="show_stored_vectors",
        help="Lädt die vollständigen Vektoren dieses Nutzers aus Qdrant.",
    )
    vectors_by_id = {}
    if show_vectors:
        with st.spinner("Gespeicherte Vektoren werden geladen ..."):
            vector_objects = load_user_objects(
                db, active_user, st.session_state.data_version, include_vectors=True
            )
        vectors_by_id = {entry["id"]: entry for entry in vector_objects}

    for entry in objects:
        with st.container(border=True):
            st.markdown(f"**{entry.get('name', 'Ohne Namen')}**")
            st.caption(f"UUID: {entry['id']}")
            st.caption(entry.get("description", "Keine Beschreibung"))
            st.markdown(metadata_chips(entry), unsafe_allow_html=True)

            if show_vectors:
                stored_entry = vectors_by_id.get(entry["id"])
                if stored_entry is None:
                    st.error("Der gespeicherte Punkt konnte in Qdrant nicht geladen werden.")
                    continue
                vector = stored_entry.get("vector")
                if vector is None:
                    st.error("Qdrant hat für diesen Punkt keinen Vektor zurückgegeben.")
                    continue
                if hasattr(vector, "tolist"):
                    vector = vector.tolist()
                with st.expander("Vollständige gespeicherte Punktdaten anzeigen"):
                    st.caption(
                        f"{len(vector)} Vektordimensionen · Original-Payload aus Qdrant"
                    )
                    st.code(
                        json.dumps(
                            {
                                "id": stored_entry["id"],
                                "payload": stored_entry["qdrant_payload"],
                                "vector": vector,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        language="json",
                    )


@st.fragment
def _render_vector_space(objects: list[dict]) -> None:
    section("Vektorraum", "PCA projiziert die Embeddings für eine interaktive 2D- oder 3D-Ansicht.")
    if len(objects) < 3:
        st.info("Für die Darstellung werden mindestens 3 Einträge benötigt.", icon=":material/scatter_plot:")
        return
    if not st.checkbox("PCA-Visualisierung laden", key="show_pca"):
        st.info("Die Berechnung startet erst nach deiner Anforderung.")
        return
    view = st.segmented_control(
        "Ansicht",
        options=["2D", "3D"],
        default="2D",
        key="vector_space_view",
        help="Die 3D-Ansicht kann mit der Maus gedreht und geneigt werden.",
    ) or "2D"
    dimensions = 3 if view == "3D" else 2
    show_search = st.toggle(
        "Suchanfrage im Vektorraum markieren",
        key="show_search_projection",
        disabled=not st.session_state.get("last_search_query", ""),
        help="Zeigt die Suchanfrage rot und die fünf besten Treffer gelb.",
    )
    with st.spinner("PCA-Projektion wird berechnet ..."):
        vector_objects = load_user_objects(db, active_user, st.session_state.data_version, include_vectors=True)
        vectors = np.array([entry["vector"] for entry in vector_objects])
        pca = PCA(n_components=dimensions).fit(vectors)
        coordinates = pca.transform(vectors)

        query_coordinate = None
        top_result_ids: set[str] = set()
        query = st.session_state.get("last_search_query", "")
        search_results = []
        if query:
            selected_category = st.session_state.get("search_category_filter", [])
            if isinstance(selected_category, str):
                selected_category = [selected_category]
            if not selected_category:
                selected_category = None
            else:
                selected_category = tuple(selected_category)
            search_results = run_user_search(
                db,
                query_text=query,
                user_id=active_user,
                limit=min(max(len(objects), 1), db.config.max_search_limit),
                data_version=st.session_state.data_version,
                category=selected_category,
                include_vectors=False,
            )
        if show_search and query:
            query_vector = np.asarray(db.embed_text(query), dtype=float).reshape(1, -1)
            query_coordinate = pca.transform(query_vector)[0]
            top_result_ids = {result["id"] for result in search_results[:5]}

    result_by_id = {
        result["id"]: {**result, "rank": rank}
        for rank, result in enumerate(search_results, start=1)
    }
    statuses = ["Top-5-Treffer" if entry["id"] in top_result_ids else "Eintrag" for entry in vector_objects]
    plot_data = pd.DataFrame(
        {
            **{axis: coordinates[:, index] for index, axis in enumerate(("x", "y", "z")[:dimensions])},
            "Name": [entry["name"] for entry in vector_objects],
            "Beschreibung": [entry["description"] for entry in vector_objects],
            "Status": statuses,
            "Rang": [result_by_id.get(entry["id"], {}).get("rank") for entry in vector_objects],
            "Cosine": [result_by_id.get(entry["id"], {}).get("score") for entry in vector_objects],
        }
    )
    if query_coordinate is not None:
        plot_data["PCA-Abstand"] = np.linalg.norm(
            coordinates - query_coordinate,
            axis=1,
        )
    else:
        plot_data["PCA-Abstand"] = None
    colors = {"Eintrag": "#94a3b8", "Top-5-Treffer": "#facc15"}
    fig = go.Figure()
    for status, color in colors.items():
        subset = plot_data[plot_data["Status"] == status]
        labels = [
            f"#{int(rank)} {name}" if pd.notna(rank) else name
            for name, rank in zip(subset["Name"], subset["Rang"], strict=True)
        ]
        customdata = subset[["Beschreibung", "Rang", "Cosine", "PCA-Abstand"]].to_numpy()
        hovertemplate = (
            "<b>%{text}</b><br>%{customdata[0]}<br>"
            "Rang: %{customdata[1]}<br>Cosine: %{customdata[2]:.3f}<br>"
            "PCA-Abstand: %{customdata[3]:.3f}<extra>%{fullData.name}</extra>"
        )
        if dimensions == 2:
            fig.add_trace(
                go.Scatter(
                    x=subset["x"],
                    y=subset["y"],
                    mode="markers+text",
                    text=labels,
                    textposition="top center",
                    name=status,
                    customdata=customdata,
                    hovertemplate=hovertemplate,
                    marker={"size": 12, "color": color, "line": {"color": "#ffffff", "width": 1}},
                )
            )
        else:
            fig.add_trace(
                go.Scatter3d(
                    x=subset["x"],
                    y=subset["y"],
                    z=subset["z"],
                    mode="markers+text",
                    text=labels,
                    textposition="top center",
                    name=status,
                    customdata=customdata,
                    hovertemplate=hovertemplate,
                    marker={"size": 7, "color": color, "line": {"color": "#ffffff", "width": 1}},
                )
            )
    if query_coordinate is not None:
        for _, result in plot_data[plot_data["Status"] == "Top-5-Treffer"].iterrows():
            if dimensions == 2:
                fig.add_trace(
                    go.Scatter(
                        x=[query_coordinate[0], result["x"]],
                        y=[query_coordinate[1], result["y"]],
                        mode="lines",
                        line={"color": "rgba(234, 179, 8, 0.45)", "width": 1},
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter3d(
                        x=[query_coordinate[0], result["x"]],
                        y=[query_coordinate[1], result["y"]],
                        z=[query_coordinate[2], result["z"]],
                        mode="lines",
                        line={"color": "rgba(234, 179, 8, 0.45)", "width": 4},
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
        query_data = {"x": [query_coordinate[0]], "y": [query_coordinate[1]]}
        if dimensions == 2:
            fig.add_trace(
                go.Scatter(
                    **query_data,
                    mode="markers+text",
                    text=[f"Suche: {query}"],
                    textposition="top center",
                    name="Suchanfrage",
                    hovertemplate="<b>Suchanfrage</b><br>%{text}<extra></extra>",
                    marker={"size": 18, "color": "#ef4444", "symbol": "star", "line": {"color": "#7f1d1d", "width": 1}},
                )
            )
        else:
            fig.add_trace(
                go.Scatter3d(
                    x=[query_coordinate[0]],
                    y=[query_coordinate[1]],
                    z=[query_coordinate[2]],
                    mode="markers+text",
                    text=[f"Suche: {query}"],
                    textposition="top center",
                    name="Suchanfrage",
                    hovertemplate="<b>Suchanfrage</b><br>%{text}<extra></extra>",
                    marker={"size": 10, "color": "#ef4444", "symbol": "diamond", "line": {"color": "#7f1d1d", "width": 1}},
                )
            )
    axis_titles = {axis: f"PCA-Achse {index}" for index, axis in enumerate(("x", "y", "z")[:dimensions], start=1)}
    fig.update_layout(
        title=f"{view}-Projektion der Einträge für {active_user}",
        **({"xaxis_title": axis_titles["x"], "yaxis_title": axis_titles["y"]} if dimensions == 2 else {"scene": {"xaxis_title": axis_titles["x"], "yaxis_title": axis_titles["y"], "zaxis_title": axis_titles["z"]}}),
    )
    st.plotly_chart(apply_chart_style(fig), width="stretch")
    explained = pca.explained_variance_ratio_.sum()
    search_caption = " Rot = Suchanfrage, gelb = fünf beste Treffer, grau = übrige Einträge." if query_coordinate is not None else ""
    st.caption(f"Die {view}-Ansicht erklärt {explained:.1%} der Varianz. Nahe Punkte sind im ursprünglichen {db.config.embedding_dimension}D-Raum tendenziell semantisch ähnlicher; die Grafik bleibt eine Projektion.{search_caption}")

    if search_results:
        st.subheader("Tatsächliches Suchranking")
        ranking_data = pd.DataFrame(
            {
                "Rang": range(1, min(5, len(search_results)) + 1),
                "Name": [result["name"] for result in search_results[:5]],
                "Cosine Similarity": [result["score"] for result in search_results[:5]],
            }
        ).sort_values("Rang", ascending=False)
        ranking_fig = px.bar(
            ranking_data,
            x="Cosine Similarity",
            y="Name",
            orientation="h",
            text="Cosine Similarity",
            color_discrete_sequence=["#facc15"],
        )
        ranking_fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        ranking_fig.update_layout(
            title=f"Ranking nach tatsächlicher {db.config.embedding_dimension}D-Cosine-Similarity",
            xaxis_title="Cosine Similarity",
            yaxis_title=None,
            showlegend=False,
        )
        st.plotly_chart(apply_chart_style(ranking_fig, height=300), width="stretch")
        st.caption("Diese Rangfolge stammt direkt aus der Suche im vollständigen Vektorraum. Die PCA-Positionen dienen nur der räumlichen Orientierung.")
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
                record_technical_event(
                    "Qdrant BATCH UPSERT",
                    f"source=demo_data\nuser_id={active_user}",
                    f"inserted={count}\nembedding=batch",
                    active_user,
                )
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
                record_technical_event(
                    "Qdrant BATCH UPSERT",
                    f"operation=reindex\nuser_id={active_user}",
                    f"updated={count}\nembedding=batch",
                    active_user,
                )
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
                record_technical_event(
                    "Qdrant DELETE",
                    f"filter=user_id:{active_user}",
                    f"deleted={count}",
                    active_user,
                )
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
                    record_technical_event(
                        "Qdrant RECREATE COLLECTION",
                        "collection=space_objects\nall_users=true",
                        f"deleted={count}\ncollection=recreated",
                        active_user,
                    )
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

entries_tab, search_tab, vector_tab, stored_tab, management_tab = st.tabs(
    ["Einträge", "Suche", "Vektorraum", "Vektordaten", "Datenverwaltung"]
)
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
with stored_tab:
    _render_stored_vectors(user_objects)
with management_tab:
    _render_data_management()
