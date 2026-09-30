"""
app_pages/multi_user.py
-------------------------
Explains the multi-user data isolation mechanism used throughout the demo.
"""

import streamlit as st

st.caption("Wie diese Demo sicherstellt, dass ein Nutzer niemals die Daten eines anderen Nutzers sieht.")

st.header("Das Problem: gemeinsame Infrastruktur, private Daten", divider="gray")
st.markdown(
    """
    In einer echten Anwendung teilen sich viele Nutzer (bzw.
    Mandanten/Organisationen) aus Kosten- und Betriebsgründen meist
    **dieselbe** Qdrant-Collection. Ohne Vorkehrungen könnte die Suche von
    Nutzer A die privaten Weltraumobjekte von Nutzer B zurückgeben. Diese
    Demo zeigt das Standardmuster, um das zu verhindern: **Payload-basiertes
    Filtern**, das bei jeder einzelnen Anfrage erzwungen wird.
    """
)

st.header("Wie es umgesetzt ist", divider="gray")
st.markdown(
    """
    Jeder Punkt in der Collection `space_objects` trägt neben `name` und
    `description` auch ein Feld `user_id` im Payload:
    """
)
st.code(
    """
{
  "id": "75807317-d514-445b-b59f-63091bf5cec8",
  "vector": [0.12, -0.04, ...],
  "payload": {
    "name": "Mars",
    "description": "Ein roter, staubiger Planet ...",
    "user_id": "Nutzer A"
  }
}
""",
    language="json",
)

st.markdown(
    "Jede Leseoperation hängt einen Qdrant-`Filter` an, der **verlangt**, "
    "dass die `user_id` des Punkts mit dem aktiven Nutzer übereinstimmt - "
    "noch bevor die Ähnlichkeitsberechnung überhaupt stattfindet:"
)
st.code(
    """
user_filter = models.Filter(
    must=[
        models.FieldCondition(
            key="user_id",
            match=models.MatchValue(value=user_id),
        )
    ]
)

# Identisch angewendet in search_data() und get_all_for_user()
response = client.query_points(
    collection_name="space_objects",
    query=query_vector,
    query_filter=user_filter,   # <- erzwingt die Trennung serverseitig
    limit=limit,
)
""",
    language="python",
)

st.header("Wo das in der App erzwungen wird", divider="gray")
st.markdown(
    """
    - **`search_data()`** - die semantische Suche bewertet nur Punkte des aktiven Nutzers.
    - **`get_all_for_user()`** - die PCA-Visualisierung lädt immer nur die Vektoren eines Nutzers.
    - **`delete_user_data()`** - der Button "Daten des aktuellen Nutzers löschen" kann mit demselben Filter (als `FilterSelector`) nur dessen Punkte entfernen.
    """
)

st.header("Warum serverseitig statt clientseitig filtern?", divider="gray")
st.markdown(
    """
    Der Filter wird an Qdrant übergeben und **innerhalb der Datenbank**
    ausgewertet, bevor Ergebnisse an die Anwendung zurückgehen. Das ist
    wichtig:
    - Die Anwendung erhält die Vektoren eines anderen Nutzers gar nicht
      erst - ein Fehler im UI-Code kann sie also nicht versehentlich
      offenlegen.
    - Es skaliert korrekt: Qdrant kann seinen Index nutzen, um nicht
      passende Punkte zu überspringen, statt alles zu durchsuchen und in
      Python zu filtern.
    - Es entspricht realen **Multi-Tenancy**-Mustern aus produktiven
      Systemen (z. B. Row-Level-Security in SQL oder Partition-Keys in
      NoSQL).
    """
)

st.info(
    "Selbst ausprobieren: Daten als **Nutzer A** anlegen, in der Seitenleiste auf "
    "**Nutzer B** wechseln und sehen, dass vorhandene Objekte, Suchergebnisse und "
    "Plot leer sind, bis Nutzer B eigene Daten hinzufügt.",
    icon=":material/lightbulb:",
)
