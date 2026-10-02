"""
app_pages/vector_db_explained.py
---------------------------------
Explains what a vector database is, how it works internally, and why it is
useful, with diagrams for an academic presentation audience.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA

from ui.components import page_header, section
from ui.theme import apply_chart_style

page_header("Vektordatenbank erklärt", "Die Theorie hinter Embeddings, Ähnlichkeitssuche und PCA.")

section("Was ist eine Vektordatenbank?", "Semantische Inhalte werden als Punkte in einem hochdimensionalen Raum gespeichert.")
st.markdown(
    """
    Eine **Vektordatenbank** speichert Daten als hochdimensionale
    Zahlenvektoren, sogenannte **Embeddings**, anstelle von (oder zusätzlich
    zu) klassischen Zeilen und Spalten. Embeddings werden von Machine-
    Learning-Modellen (z. B. Sentence-Transformers) erzeugt, die Text,
    Bilder oder Audio auf einen Punkt im Vektorraum abbilden - so, dass
    **semantisch ähnliche Eingaben nah beieinander landen**. Statt exakter
    Treffer wie bei SQL (`WHERE name = 'Mars'`) beantwortet eine
    Vektordatenbank die Frage **"was ist dem hier am ähnlichsten?"**, indem
    sie den Abstand zwischen Vektoren misst.
    """
)

section("Ablauf von Anfang bis Ende", "So läuft ein Einfüge- und Suchvorgang in dieser Demo ab.")
st.markdown("So läuft in dieser Demo jeder Einfüge- und jeder Suchvorgang ab:")
st.mermaid_chart(
    """
    flowchart LR
        A["Text\\n'Eine Person mit technischem Beruf'"] --> B["Embedding-Modell\\n(paraphrase-multilingual-MiniLM-L12-v2)"]
        B --> C["Vektor\\n[0.12, -0.04, ..., 0.31]\\n(384 Dimensionen)"]
        C --> D[("Qdrant-Collection\\n'space_objects'")]
        E["Suchanfrage-Text"] --> B
        D -->|Kosinus-Ähnlichkeitssuche| F["Sortierte Ergebnisse\\nmit Ähnlichkeitswerten"]
    """
)

section("Wie die Ähnlichkeitssuche funktioniert", "Qdrant vergleicht Vektoren anhand ihrer Kosinus-Ähnlichkeit.")
st.markdown(
    """
    Sobald ein Text als Vektor vorliegt, vergleicht Qdrant den
    Anfrage-Vektor mit jedem gespeicherten Vektor anhand eines
    Abstandsmaßes - in dieser Demo die **Kosinus-Ähnlichkeit**, die den
    Winkel zwischen zwei Vektoren misst, unabhängig von deren Länge.
    Vektoren, die in eine ähnliche "Richtung" im Embedding-Raum zeigen,
    stehen für ähnliche Bedeutungen und erhalten einen Ähnlichkeitswert nahe
    `1.0`. Intern nutzt Qdrant einen approximativen Nächste-Nachbarn-Index
    (HNSW), damit das auch bei Millionen von Vektoren schnell bleibt, statt
    jeden Punkt einzeln zu vergleichen.
    """
)

section("Relationale Datenbank oder Vektordatenbank?", "Beide Systeme lösen unterschiedliche Arten von Suchaufgaben.")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Relationale Datenbank", divider="gray")
    st.markdown(
        """
        - Findet **exakte oder Muster**-Treffer (`LIKE '%Sturm%'`)
        - Kennt keine *Bedeutung*
        - Übersieht Synonyme und Umschreibungen komplett
        - Sehr gut für strukturierte, tabellarische Daten
        """
    )
with col2:
    st.subheader("Vektordatenbank", divider="gray")
    st.markdown(
        """
        - Findet **semantisch ähnliche** Elemente
        - Erkennt, dass "ein roter Planet mit Stürmen" zu "Mars" passt
        - Sortiert Ergebnisse nach Ähnlichkeitswert
        - Sehr gut für unstrukturierte Daten: Text, Bilder, Audio
        """
    )

section("Live-Beispiel: Clustering nach Bedeutung", "Eine feste Illustration zeigt, wie Gruppen im Vektorraum entstehen.")
st.markdown(
    "Eine kleine, feste Menge an Beispielbegriffen, eingebettet und mit PCA auf 2D projiziert, "
    "um Clustering unabhängig von deinen eigenen gespeicherten Daten zu veranschaulichen:"
)


@st.cache_data
def build_illustration_plot() -> pd.DataFrame:
    """Builds a tiny illustrative point cloud without touching the live
    database, so this page works even with an empty collection."""
    # Pre-computed toy 4D "embeddings" standing in for real 384D vectors,
    # deliberately grouped so the four example categories form visible clusters.
    rng = np.random.default_rng(seed=42)
    category_terms = {
        "Menschen": ["Ärztin", "Lehrer", "Fotograf", "Architektin"],
        "Studierende": ["Informatikstudentin", "Maschinenbaustudent", "Psychologiestudentin", "Biologiestudent"],
        "Gegenstände": ["Kaffeemaschine", "Fahrrad", "Lampe", "Bücher"],
        "Möbel": ["Schreibtisch", "Bürostuhl", "Bücherregal", "Sofa"],
    }
    category_centers = {
        "Menschen": (2.0, 2.0),
        "Studierende": (2.0, -2.0),
        "Gegenstände": (-2.0, 2.0),
        "Möbel": (-2.0, -2.0),
    }

    vectors_list = []
    labels = []
    categories = []
    for category, terms in category_terms.items():
        center_x, center_y = category_centers[category]
        center = np.array([center_x, center_y, 0.0, 0.0])
        vectors_list.append(rng.normal(loc=center, scale=0.3, size=(len(terms), 4)))
        labels.extend(terms)
        categories.extend([category] * len(terms))

    vectors = np.vstack(vectors_list)

    coords_2d = PCA(n_components=2).fit_transform(vectors)
    return pd.DataFrame(
        {"x": coords_2d[:, 0], "y": coords_2d[:, 1], "label": labels, "category": categories}
    )


df_illustration = build_illustration_plot()
fig = px.scatter(
    df_illustration,
    x="x",
    y="y",
    color="category",
    text="label",
    title="Illustrative Embedding-Cluster (Beispieldaten)",
)
fig.update_traces(textposition="top center", marker=dict(size=12))
st.plotly_chart(apply_chart_style(fig), width="stretch")
st.caption(
    "Die vier Beispielgruppen liegen in unterschiedlichen Bereichen: Menschen, "
    "Studierende, Gegenstände und Möbel. Die Kategorien dienen hier nur zur "
    "Lesbarkeit der künstlichen Illustration."
)

