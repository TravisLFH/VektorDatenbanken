"""
streamlit_app.py
-----------------
Entry point for the "Planets and Space Objects" Vector Database demo.

Sets up the shared Qdrant connection, the active-user selector, and the
data-management ("danger zone") controls in the sidebar, then hands off to
the selected page. All pages read `st.session_state.db` and
`st.session_state.active_user`.
"""

import streamlit as st

from database import VectorDBManager

st.set_page_config(page_title="Weltraumobjekte Vektordatenbank Demo", layout="wide", page_icon=":material/public:")


@st.cache_resource
def get_db_manager() -> VectorDBManager:
    """Creates a single shared DB connection + embedding model for the app
    session (loading the embedding model is expensive, so we cache it)."""
    manager = VectorDBManager()
    manager.create_collection()
    return manager


st.session_state.db = get_db_manager()

# ---------------------------------------------------------------------------
# Sidebar: active user selection (drives multi-user filtering on every page)
# ---------------------------------------------------------------------------
st.sidebar.header("Aktiver Nutzer", divider="gray")
st.session_state.active_user = st.sidebar.selectbox(
    "Aktiven Nutzer wählen", ["Nutzer A", "Nutzer B"], label_visibility="collapsed"
)
st.sidebar.caption(
    f"Alle angezeigten Daten sind auf **{st.session_state.active_user}** gefiltert. "
    "Qdrant erzwingt diese Trennung serverseitig über einen Payload-Filter auf `user_id`."
)

# ---------------------------------------------------------------------------
# Sidebar: data management ("danger zone")
# ---------------------------------------------------------------------------
with st.sidebar.expander("Datenverwaltung", icon=":material/database:"):
    if st.button("Demodaten für aktuellen Nutzer hinzufügen", icon=":material/auto_awesome:", width="stretch"):
        count = st.session_state.db.seed_demo_data(st.session_state.active_user)
        st.toast(f"{count} Beispieldaten für {st.session_state.active_user} eingefügt.")
        st.rerun()

    if st.button("Daten des aktuellen Nutzers löschen", icon=":material/person_remove:", width="stretch"):
        st.session_state.db.delete_user_data(st.session_state.active_user)
        st.toast(f"Alle Daten von {st.session_state.active_user} wurden gelöscht.")
        st.rerun()

    if st.button("ALLE Daten löschen (alle Nutzer)", icon=":material/delete_forever:", width="stretch"):
        st.session_state.db.delete_all_data()
        st.toast("Alle Daten aller Nutzer wurden gelöscht.")
        st.rerun()

    st.caption(f"Gespeicherte Objekte insgesamt (alle Nutzer): **{st.session_state.db.count_all()}**")

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
page = st.navigation(
    [
        st.Page("app_pages/demo.py", title="Interaktive Demo", icon=":material/rocket_launch:"),
        st.Page("app_pages/features.py", title="Funktionen", icon=":material/checklist:"),
        st.Page("app_pages/vector_db_explained.py", title="Wie Vektordatenbanken funktionieren", icon=":material/hub:"),
        st.Page("app_pages/multi_user.py", title="Mehrbenutzer-Trennung", icon=":material/group:"),
    ],
    position="top",
)

st.title(page.title, icon=page.icon)
page.run()

