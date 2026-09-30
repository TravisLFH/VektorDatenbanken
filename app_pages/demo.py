"""
app_pages/demo.py
-----------------
Interactive demo page: insert/update space objects, run semantic search,
visualize the vector space, and manage demo data - all scoped to the
active user selected in the sidebar (see streamlit_app.py).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA

db = st.session_state.db
active_user = st.session_state.active_user

st.caption("Daten anlegen, semantisch suchen und den Vektorraum für den aktuell aktiven Nutzer betrachten.")

# ---------------------------------------------------------------------------
# Section: Data entry (insert new object or update an existing one)
# ---------------------------------------------------------------------------
st.header("1. Weltraumobjekt anlegen oder bearbeiten", divider="gray")

# Keep track of which point (by UUID) is being edited, if any.
if "editing_point_id" not in st.session_state:
    st.session_state.editing_point_id = None

with st.form("data_entry_form", clear_on_submit=False):
    col1, col2 = st.columns([1, 2])
    with col1:
        planet_name = st.text_input("Name", key="form_name")
    with col2:
        planet_description = st.text_area("Beschreibung", key="form_description")

    button_row = st.container(horizontal=True)
    insert_clicked = button_row.form_submit_button("Als neu einfügen", icon=":material/add:")
    update_clicked = button_row.form_submit_button("Auswahl aktualisieren", icon=":material/edit:")

    if insert_clicked:
        if planet_name and planet_description:
            new_id = db.insert_data(planet_name, planet_description, active_user)
            st.success(f"'{planet_name}' für {active_user} eingefügt (ID: {new_id})")
        else:
            st.warning("Bitte Name und Beschreibung angeben.")

    if update_clicked:
        if not st.session_state.editing_point_id:
            st.warning("Bitte zuerst ein Objekt aus der Tabelle unten auswählen.")
        elif planet_name and planet_description:
            db.update_data(
                st.session_state.editing_point_id,
                planet_name,
                planet_description,
                active_user,
            )
            st.success(f"'{planet_name}' wurde aktualisiert.")
        else:
            st.warning("Bitte Name und Beschreibung angeben.")

# ---------------------------------------------------------------------------
# Section: Browse existing objects for the active user (select to edit)
# ---------------------------------------------------------------------------
st.header("2. Vorhandene Objekte des aktuellen Nutzers", divider="gray")

user_objects = db.get_all_for_user(active_user)

# Precompute the 2D PCA projection once so it can be reused both by the
# per-object vector inspector below and by the plot in section 4.
coords_2d_by_id = {}
if len(user_objects) >= 2:
    vectors = [o["vector"] for o in user_objects]
    coords_2d = PCA(n_components=2).fit_transform(vectors)
    coords_2d_by_id = {o["id"]: coords_2d[i] for i, o in enumerate(user_objects)}

if user_objects:
    df_objects = pd.DataFrame(
        [{"id": o["id"], "name": o["name"], "description": o["description"]} for o in user_objects]
    )
    selected_name = st.selectbox(
        "Objekt zum Bearbeiten in das Formular laden",
        ["-- keine Auswahl --"] + df_objects["name"].tolist(),
    )
    if selected_name != "-- keine Auswahl --":
        selected_row = df_objects[df_objects["name"] == selected_name].iloc[0]
        st.session_state.editing_point_id = selected_row["id"]
        st.caption(f"Bearbeitete Punkt-ID: `{selected_row['id']}`")

        show_vector = st.toggle("Vollständigen Vektor des ausgewählten Objekts anzeigen", key="show_vector")
        if show_vector:
            view_mode = st.segmented_control(
                "Ansicht",
                ["384D (Rohvektor)", "2D (PCA-Projektion)"],
                default="384D (Rohvektor)",
                label_visibility="collapsed",
            )
            selected_object = next(o for o in user_objects if o["id"] == selected_row["id"])

            if view_mode == "384D (Rohvektor)":
                vector = np.array(selected_object["vector"])
                st.caption(f"{len(vector)} Dimensionen - der vollständige Embedding-Vektor, wie er in Qdrant gespeichert ist.")
                df_vector = pd.DataFrame({"Dimension": range(len(vector)), "Wert": vector})
                st.dataframe(df_vector, width="stretch", hide_index=True, height=250)
            else:
                if selected_row["id"] in coords_2d_by_id:
                    x, y = coords_2d_by_id[selected_row["id"]]
                    st.caption("Die gleiche PCA-Projektion, die auch im Streudiagramm in Abschnitt 4 verwendet wird.")
                    col_x, col_y = st.columns(2)
                    col_x.metric("x", f"{x:.4f}")
                    col_y.metric("y", f"{y:.4f}")
                else:
                    st.info("Für die 2D-Projektion werden mindestens 2 Objekte für diesen Nutzer benötigt.")
    else:
        st.session_state.editing_point_id = None

    st.dataframe(df_objects[["name", "description"]], width="stretch", hide_index=True)
else:
    st.info(f"Für {active_user} sind noch keine Weltraumobjekte gespeichert. Oben eines anlegen oder den Demodaten-Button in der Seitenleiste nutzen.")

# ---------------------------------------------------------------------------
# Section: Semantic search
# ---------------------------------------------------------------------------
st.header("3. Semantische Suche", divider="gray")

query = st.text_input(
    "Nach Bedeutung suchen",
    placeholder="z. B. 'ein roter Planet mit Stürmen'",
    label_visibility="collapsed",
)

if query:
    results = db.search_data(
        query_text=query,
        user_id=active_user,
        limit=max(len(user_objects), 1),
    )
    if results:
        df_results = pd.DataFrame(results)[["name", "description", "score"]]
        df_results["score"] = df_results["score"].round(4)
        st.dataframe(df_results, width="stretch", hide_index=True)

        st.subheader("Vektoren von Suchanfrage und Treffern", divider="gray")
        st.caption(
            "Die Suchanfrage wird als eigener Vektor dargestellt. Je näher ein Treffer "
            "an ihr liegt, desto höher ist normalerweise sein Qdrant-Ähnlichkeitswert."
        )
        vector_view = st.segmented_control(
            "Vektoransicht",
            ["384D (Wertevergleich)", "2D (gemeinsame PCA-Projektion)"],
            default="2D (gemeinsame PCA-Projektion)",
            key="search_vector_view",
        )

        query_vector = np.array(db.embed_text(query))
        result_vectors = [np.array(result["vector"]) for result in results]

        if vector_view == "384D (Wertevergleich)":
            vector_labels = ["Suchanfrage"] + [
                f"{result['name']} (Treffer {index})"
                for index, result in enumerate(results, start=1)
            ]
            vector_matrix = np.vstack([query_vector, *result_vectors])
            dimensions = np.arange(1, vector_matrix.shape[1] + 1)
            df_vector_values = pd.DataFrame(vector_matrix.T, columns=vector_labels)
            df_vector_values.insert(0, "Dimension", dimensions)

            st.caption(
                f"Alle {vector_matrix.shape[1]} Dimensionen. Gleiche Kurvenverläufe "
                "bedeuten ähnliche Embedding-Muster."
            )
            df_vector_long = df_vector_values.melt(
                id_vars="Dimension", var_name="Vektor", value_name="Wert"
            )
            fig_vectors = px.line(
                df_vector_long,
                x="Dimension",
                y="Wert",
                color="Vektor",
                title="Werteverlauf über alle Embedding-Dimensionen",
            )
            st.plotly_chart(fig_vectors, width="stretch")
            st.dataframe(df_vector_values.round(6), width="stretch", hide_index=True, height=260)
        else:
            # PCA projects the query and all returned vectors using one shared basis.
            vector_matrix = np.vstack([query_vector, *result_vectors])
            coords_search = PCA(n_components=2).fit_transform(vector_matrix)
            df_search_plot = pd.DataFrame(
                {
                    "x": coords_search[:, 0],
                    "y": coords_search[:, 1],
                    "Bezeichnung": ["Suchanfrage"] + [result["name"] for result in results],
                    "Kategorie": ["Suchanfrage"] + [
                        "Bester Treffer"
                        if index == 1
                        else "Top 5"
                        if index <= 5
                        else "Unter Top 5"
                        for index in range(1, len(results) + 1)
                    ],
                    "Typ": ["Suchanfrage"] + ["Treffer"] * len(results),
                    "Ähnlichkeit": [None] + [round(result["score"], 4) for result in results],
                    "Beschreibung": [query] + [result["description"] for result in results],
                }
            )
            fig_search = px.scatter(
                df_search_plot,
                x="x",
                y="y",
                color="Kategorie",
                symbol="Typ",
                text="Bezeichnung",
                hover_data={
                    "Beschreibung": True,
                    "Ähnlichkeit": True,
                    "x": False,
                    "y": False,
                },
                color_discrete_map={
                    "Suchanfrage": "#2563eb",
                    "Bester Treffer": "#16a34a",
                    "Top 5": "#eab308",
                    "Unter Top 5": "#dc2626",
                },
                title="Suchanfrage und Treffer im gemeinsamen 2D-Vektorraum",
            )
            fig_search.update_traces(textposition="top center", marker=dict(size=13))
            st.plotly_chart(fig_search, width="stretch")
            st.dataframe(
                df_search_plot[["Bezeichnung", "Kategorie", "x", "y", "Ähnlichkeit"]].round(4),
                width="stretch",
                hide_index=True,
            )
    else:
        st.info("Keine Ergebnisse für diesen Nutzer gefunden.")

# ---------------------------------------------------------------------------
# Section: 2D vector visualization via PCA
# ---------------------------------------------------------------------------
st.header("4. Vektorraum-Visualisierung (PCA)", divider="gray")

if len(user_objects) >= 2:
    names = [o["name"] for o in user_objects]
    descriptions = [o["description"] for o in user_objects]
    coords_2d = np.array([coords_2d_by_id[o["id"]] for o in user_objects])

    df_plot = pd.DataFrame(
        {
            "x": coords_2d[:, 0],
            "y": coords_2d[:, 1],
            "name": names,
            "description": descriptions,
        }
    )

    fig = px.scatter(
        df_plot,
        x="x",
        y="y",
        text="name",
        hover_data={"description": True, "x": False, "y": False},
        title=f"2D-Projektion der Embeddings für {active_user}",
    )
    fig.update_traces(textposition="top center", marker=dict(size=12))
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Punkte, die nahe beieinander liegen, stehen für Weltraumobjekte mit "
        "semantisch ähnlichen Beschreibungen - das ist der Kern dessen, wie eine "
        "Vektordatenbank Informationen organisiert."
    )
else:
    st.info("Mindestens 2 Weltraumobjekte für diesen Nutzer anlegen, um den PCA-Plot zu sehen.")


