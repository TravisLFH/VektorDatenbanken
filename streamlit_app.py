"""
streamlit_app.py
-----------------
Entry point for the "Planets and Space Objects" Vector Database demo.

Sets up the shared Qdrant connection, the active-user selector, and the
data-management ("danger zone") controls in the sidebar, then hands off to
the selected page. All pages read `st.session_state.db` and
`st.session_state.active_user`.
"""

import logging

import streamlit as st

class _OptionalTorchvisionWatcherFilter(logging.Filter):
    """Suppress repeated Streamlit probes for unused Transformers vision modules."""

    def __init__(self) -> None:
        super().__init__()
        self.reported = False

    def filter(self, record: logging.LogRecord) -> bool:
        exception = record.exc_info[1] if record.exc_info else None
        is_optional_vision_probe = (
            record.name == "streamlit.watcher.local_sources_watcher"
            and record.getMessage().startswith("Examining the path of transformers.models.")
            and isinstance(exception, ModuleNotFoundError)
            and exception.name == "torchvision"
        )
        if not is_optional_vision_probe:
            return True

        if not self.reported:
            logging.getLogger(__name__).info(
                "Streamlit prüft optionale Transformers-Bildmodule; torchvision wird "
                "von dieser Textsuche nicht benötigt. Wiederholte Watcher-Meldungen "
                "dazu werden ausgeblendet."
            )
            self.reported = True
        return False


_watcher_logger = logging.getLogger("streamlit.watcher.local_sources_watcher")
if not getattr(_watcher_logger, "_optional_torchvision_filter_installed", False):
    _watcher_logger.addFilter(_OptionalTorchvisionWatcherFilter())
    setattr(_watcher_logger, "_optional_torchvision_filter_installed", True)

from app_state import init_state, record_activity, reset_user_state
from database import VectorDBManager
from errors import CollectionConfigurationError, DatabaseUnavailableError, EmbeddingModelError
from ui.components import activity_log, hot_reload_timer, technical_console

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Vektordatenbank Demo", layout="wide", page_icon=":material/public:")
init_state()


@st.cache_resource
def get_db_manager() -> VectorDBManager:
    """Creates a single shared DB connection + embedding model for the app
    session (loading the embedding model is expensive, so we cache it)."""
    manager = VectorDBManager()
    manager.create_collection()
    manager.warm_up_model()
    return manager


try:
    with st.spinner("Embedding-Modell wird aus dem Cache geladen oder bei Bedarf heruntergeladen ..."):
        st.session_state.db = get_db_manager()
except EmbeddingModelError as exc:
    logger.warning("Embedding-Modell konnte nicht initialisiert werden: %s", exc)
    st.error("Das Embedding-Modell konnte nicht geladen oder heruntergeladen werden.")
    st.info("Prüfe die Internetverbindung und den Hugging-Face-Modell-Cache, und versuche es erneut.")
    if st.button("Erneut versuchen", icon=":material/refresh:"):
        get_db_manager.clear()
        st.rerun()
    st.stop()
except (DatabaseUnavailableError, CollectionConfigurationError) as exc:
    logger.warning("Datenbankinitialisierung fehlgeschlagen: %s", exc)
    st.error("Qdrant ist derzeit nicht erreichbar oder inkompatibel.")
    st.info("Starte den Dienst mit `docker compose up -d` und prüfe anschließend erneut.")
    if st.button("Verbindung erneut prüfen", icon=":material/refresh:"):
        get_db_manager.clear()
        st.rerun()
    st.stop()

def _on_user_change() -> None:
    selected_user = st.session_state.active_user_selector
    if selected_user != st.session_state.active_user:
        st.session_state.active_user = selected_user
        record_activity("Nutzerwechsel", f"Ansicht auf {selected_user} gewechselt.", selected_user)
        reset_user_state()


# ---------------------------------------------------------------------------
# Sidebar: active user selection (drives multi-user filtering on every page)
# ---------------------------------------------------------------------------
st.sidebar.header("Aktiver Nutzer", divider="gray")
st.sidebar.selectbox(
    "Aktiven Nutzer wählen",
    ["Nutzer A", "Nutzer B"],
    key="active_user_selector",
    on_change=_on_user_change,
    label_visibility="collapsed",
)
st.sidebar.caption(
    f"Alle angezeigten Daten sind auf **{st.session_state.active_user}** gefiltert. "
    "Qdrant erzwingt diese Trennung serverseitig über einen Payload-Filter auf `user_id`."
)
with st.sidebar:
    activity_log()
    technical_console()

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
page = st.navigation(
    [
        st.Page("app_pages/demo.py", title="Interaktive Demo", icon=":material/rocket_launch:"),
    ],
    position="top",
)

page.run()
hot_reload_timer()
