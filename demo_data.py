"""Lädt die Demo-Datensätze und Beispielanfragen aus ``demo_daten.md``."""

from __future__ import annotations

from pathlib import Path
from runpy import run_path
from typing import Any


_DATA_FILE = Path(__file__).with_name("demo_daten.md")
_DATA: dict[str, Any] = run_path(str(_DATA_FILE))

DEMO_SUCHANFRAGEN: tuple[str, ...] = tuple(_DATA["DEMO_SUCHANFRAGEN"])


def iter_demo_entries() -> list[tuple[str, str]]:
    """Liefert alle Demo-Einträge aus den Gruppen und den Grenzfällen."""
    entries = [
        (name, description)
        for items in _DATA["DEMO_DATEN"].values()
        for name, description in items
    ]
    entries.extend(_DATA["GRENZFAELLE"])
    return entries