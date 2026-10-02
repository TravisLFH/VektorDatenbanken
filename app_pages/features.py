"""
app_pages/features.py
----------------------
Describes every feature of the demo application in plain language, for
audiences who are new to vector databases.
"""

import streamlit as st

from ui.components import page_header, section

page_header("Funktionen", "Ein kompakter Überblick über die Arbeitsweise und Möglichkeiten dieser Demo.")

section("Dateneingabe und Embedding", "Wie aus Text ein durchsuchbarer Eintrag wird.")
st.markdown(
    """
    Auf der Seite **Interaktive Demo** kannst du den **Namen** und eine
    frei formulierte **Beschreibung** eines Planeten oder Weltraumobjekts
    eingeben. Beim Klick auf *Als neu einfügen* wird der Rohtext nicht
    einfach so für die Suche gespeichert - er wird zunächst in ein
    **Vektor-Embedding** umgewandelt: eine Liste von Zahlen (in dieser
    Demo 384 Stück), die die *Bedeutung* des Textes repräsentiert. Dieses
    Embedding wird zusammen mit dem Originaltext als Metadaten ("Payload")
    als ein Punkt in der Qdrant-Collection `space_objects` gespeichert.
    """
)

section("Einträge bearbeiten", "Änderungen bleiben über die UUID eindeutig zugeordnet.")
st.markdown(
    """
    Wählst du ein bestehendes Objekt aus der Tabelle aus, wird es zurück in
    das Formular geladen. Ein Klick auf *Auswahl aktualisieren* überschreibt
    dessen Payload **und** berechnet das Embedding aus der neuen Beschreibung
    neu - über die stabile UUID des Objekts als Schlüssel. Das zeigt, dass
    Vektordatenbanken vollständige CRUD-Operationen unterstützen, nicht nur
    das Einfügen.
    """
)

section("Semantische Suche", "Suche nach Bedeutung statt nur nach Wörtern.")
st.markdown(
    """
    Das Suchfeld sucht nicht nach passenden Schlüsselwörtern. Deine Anfrage
    wird mit demselben Modell wie beim Speichern in ein Embedding umgewandelt,
    und Qdrant findet die gespeicherten Vektoren, die **inhaltlich am
    ähnlichsten** sind (Kosinus-Ähnlichkeit). Deshalb kann eine Suche nach
    *"ein roter Planet mit Stürmen"* **Mars** finden, selbst wenn das Wort
    "Sturm" nie wörtlich vorkommt - weil die Konzepte inhaltlich
    übereinstimmen. Jedes Ergebnis enthält einen **Ähnlichkeitswert**
    zwischen 0 und 1.
    """
)

section("Vektorraum-Visualisierung", "PCA macht hochdimensionale Embeddings sichtbar.")
st.markdown(
    """
    Embeddings haben in dieser Demo 384 Dimensionen - unmöglich, sie direkt
    darzustellen. Die App nutzt **PCA (Principal Component Analysis)**, um
    jeden Vektor auf nur 2 Dimensionen zu reduzieren und dabei möglichst
    viel der ursprünglichen Struktur zu erhalten, und stellt das Ergebnis
    mit Plotly dar. Objekte, die im 2D-Plot nahe beieinander liegen, sind im
    ursprünglichen 384D-Raum semantisch ähnlich - ein visueller Beweis
    dafür, dass die Datenbank Informationen nach *Bedeutung* organisiert.
    """
)

section("Mehrbenutzer-Datentrennung", "Jeder Nutzer sieht ausschließlich seine eigenen Einträge.")
st.markdown(
    """
    Jede Operation - Einfügen, Aktualisieren, Suchen und Visualisieren - ist
    auf den in der Seitenleiste gewählten Nutzer beschränkt. Siehe die Seite
    **Mehrbenutzer-Trennung** für eine detaillierte Erklärung, wie das
    umgesetzt ist.
    """
)

section("Datenverwaltung", "Demo-Daten, Re-Embedding und bestätigte Löschaktionen.")
st.markdown(
    """
    Das Panel **Datenverwaltung** in der Seitenleiste erlaubt einen
    schnellen Reset der Demo:
    - **Demodaten für aktuellen Nutzer hinzufügen** fügt eine kuratierte
      Auswahl an Beispiel-Planeten, -Monden und -Sternen ein, damit sofort
      genug Daten für Suche und Cluster-Visualisierung vorhanden sind.
    - **Daten des aktuellen Nutzers löschen** entfernt nur die Punkte des
      aktiven Nutzers.
    - **ALLE Daten löschen** leert die gesamte Collection, für alle Nutzer.
    """
)

