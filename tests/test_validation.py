from __future__ import annotations

import pytest

from errors import ValidationError
from validation import validate_point_id, validate_search_limit, validate_text, validate_user_id


def test_validation_accepts_normal_values() -> None:
    assert validate_user_id("Nutzer A") == "Nutzer A"
    assert validate_text("  Mars ", "Name", 20) == "Mars"
    assert validate_point_id("550e8400-e29b-41d4-a716-446655440000")
    assert validate_search_limit(5, maximum=10) == 5


@pytest.mark.parametrize(
    "operation",
    [
        lambda: validate_user_id("Fremd"),
        lambda: validate_text(" ", "Name", 20),
        lambda: validate_text("x" * 21, "Name", 20),
        lambda: validate_point_id("keine-uuid"),
        lambda: validate_search_limit(0, maximum=10),
    ],
)
def test_validation_rejects_invalid_values(operation) -> None:
    with pytest.raises(ValidationError):
        operation()
