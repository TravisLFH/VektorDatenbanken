"""Anwendungsfehler mit verständlicher Trennung von Ursache und UI-Meldung."""

from __future__ import annotations


class VectorDatabaseError(Exception):
    """Basisklasse für erwartbare Fehler der Anwendung."""


class DatabaseUnavailableError(VectorDatabaseError):
    """Qdrant ist nicht erreichbar oder nicht korrekt initialisiert."""


class CollectionConfigurationError(VectorDatabaseError):
    """Die bestehende Collection hat inkompatible Vektoreinstellungen."""


class ValidationError(VectorDatabaseError):
    """Eine Eingabe erfüllt die fachlichen Grenzen nicht."""


class EntryNotFoundError(VectorDatabaseError):
    """Der angeforderte Eintrag existiert nicht mehr."""


class EmbeddingModelError(VectorDatabaseError):
    """Das Embedding-Modell konnte nicht geladen oder verwendet werden."""
