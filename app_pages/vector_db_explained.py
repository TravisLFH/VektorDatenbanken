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

st.caption("Die Theorie hinter dieser Demo: was Vektordatenbanken sind und wie sie ähnliche Elemente finden.")

st.header("Was ist eine Vektordatenbank?", divider="gray")
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

st.header("Ablauf von Anfang bis Ende", divider="gray")
st.markdown("So läuft in dieser Demo jeder Einfüge- und jeder Suchvorgang ab:")
st.mermaid_chart(
    """
    flowchart LR
        A["Text\\n'Ein roter Planet mit Stürmen'"] --> B["Embedding-Modell\\n(all-MiniLM-L6-v2)"]
        B --> C["Vektor\\n[0.12, -0.04, ..., 0.31]\\n(384 Dimensionen)"]
        C --> D[("Qdrant-Collection\\n'space_objects'")]
        E["Suchanfrage-Text"] --> B
        D -->|Kosinus-Ähnlichkeitssuche| F["Sortierte Ergebnisse\\nmit Ähnlichkeitswerten"]
    """
)

st.header("Wie die Ähnlichkeitssuche funktioniert", divider="gray")
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

st.header("Warum nicht einfach eine normale (relationale) Datenbank?", divider="gray")
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

st.header("Live-Beispiel: Clustering nach Bedeutung", divider="gray")
st.markdown(
    "Eine kleine, feste Menge an Beispielbegriffen, eingebettet und mit PCA auf 2D projiziert, "
    "um Clustering unabhängig von deinen eigenen gespeicherten Daten zu veranschaulichen:"
)


@st.cache_data
def build_illustration_plot() -> pd.DataFrame:
    """Builds a tiny illustrative point cloud without touching the live
    database, so this page works even with an empty collection."""
    # Pre-computed toy 4D "embeddings" standing in for real 384D vectors,
    # deliberately grouped so planets/space and fruits form visible clusters.
    rng = np.random.default_rng(seed=42)
    space_terms = ["Mars", "Jupiter", "Saturn", "Komet", "Galaxie"]
    fruit_terms = ["Apfel", "Banane", "Orange", "Traube", "Mango"]

    space_points = rng.normal(loc=2.0, scale=0.3, size=(len(space_terms), 4))
    fruit_points = rng.normal(loc=-2.0, scale=0.3, size=(len(fruit_terms), 4))

    vectors = np.vstack([space_points, fruit_points])
    labels = space_terms + fruit_terms
    categories = ["Weltraumobjekt"] * len(space_terms) + ["Frucht"] * len(fruit_terms)

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
st.plotly_chart(fig, width="stretch")
st.caption(
    "Man erkennt zwei klare Cluster: Weltraumobjekte gruppieren sich, Früchte "
    "gruppieren sich - obwohl keine explizite Kategorie zur Platzierung genutzt wurde."
)

