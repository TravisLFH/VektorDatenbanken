"""Zentrale Validierung für Nutzer, Texte, UUIDs und Suchlimits."""

from __future__ import annotations

from uuid import UUID

from config import USERS
from errors import ValidationError


def validate_user_id(user_id: str) -> str:
    """Akzeptiert ausschließlich die festgelegten Demo-Nutzer."""
    if user_id not in USERS:
        raise ValidationError("Unbekannter Nutzer.")
    return user_id


def validate_text(value: str, field_name: str, maximum_length: int) -> str:
    """Trimmt Text und prüft Pflichtfeld sowie maximale Länge."""
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{field_name} darf nicht leer sein.")
    if len(normalized) > maximum_length:
        raise ValidationError(
            f"{field_name} darf höchstens {maximum_length} Zeichen enthalten "
            f"(aktuell: {len(normalized)})."
        )
    return normalized


def validate_point_id(point_id: str) -> str:
    """Prüft eine Punkt-ID und gibt sie kanonisch als UUID-Text zurück."""
    try:
        return str(UUID(str(point_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError("Die Objekt-ID ist keine gültige UUID.") from exc


def validate_search_limit(limit: int, maximum: int = 50) -> int:
    """Begrenzt Suchlimits auf einen positiven, sinnvollen Bereich."""
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= maximum:
        raise ValidationError(f"Das Suchlimit muss zwischen 1 und {maximum} liegen.")
    return limit
