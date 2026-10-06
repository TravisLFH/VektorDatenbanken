from __future__ import annotations

import pytest

from config import AppConfig
from database import VectorDBManager
from errors import EntryNotFoundError


class VectorValue(list[float]):
    def tolist(self) -> list[float]:
        return list(self)


class TestEncoder:
    def encode(self, value, batch_size=32):
        if isinstance(value, str):
            return VectorValue([float(len(value)), 1.0, 0.0])
        return [VectorValue([float(len(text)), 1.0, 0.0]) for text in value]


def make_manager(fake_client) -> VectorDBManager:
    return VectorDBManager(
        config=AppConfig(embedding_dimension=3),
        client=fake_client,
        encoder=TestEncoder(),
    )


def test_user_filter_isolation_for_list_update_and_delete(fake_client) -> None:
    manager = make_manager(fake_client)
    point_a = manager.insert_data("Mars", "Roter Planet", "Nutzer A")
    point_b = manager.insert_data("Jupiter", "Gasriese", "Nutzer B")

    assert [item["id"] for item in manager.get_all_for_user("Nutzer A")] == [point_a]
    assert [item["id"] for item in manager.get_all_for_user("Nutzer B")] == [point_b]

    with pytest.raises(EntryNotFoundError):
        manager.update_data(point_b, "Manipuliert", "Darf nicht gespeichert werden", "Nutzer A")
    with pytest.raises(EntryNotFoundError):
        manager.delete_data(point_b, "Nutzer A")

    assert point_b in fake_client.points
    assert fake_client.points[point_b].payload["user_id"] == "Nutzer B"


def test_get_all_for_user_returns_full_stored_payload_and_vector(fake_client) -> None:
    manager = make_manager(fake_client)
    point_id = manager.insert_data(
        "Mars",
        "Roter Planet",
        "Nutzer A",
        metadata={"category": ["Planet"]},
    )
    manager.insert_data("Jupiter", "Gasriese", "Nutzer B")

    stored_points = manager.get_all_for_user("Nutzer A", include_vectors=True)

    assert len(stored_points) == 1
    stored_point = stored_points[0]
    assert stored_point["id"] == point_id
    assert stored_point["qdrant_payload"] == fake_client.points[point_id].payload
    assert stored_point["vector"] == fake_client.points[point_id].vector


def test_delete_requires_uuid_and_user(fake_client) -> None:
    manager = make_manager(fake_client)
    point_id = manager.insert_data("Mars", "Roter Planet", "Nutzer A")

    manager.delete_data(point_id, "Nutzer A")

    assert point_id not in fake_client.points


def test_metadata_is_stored_separately_from_embedding(fake_client) -> None:
    manager = make_manager(fake_client)

    point_id = manager.insert_data(
        "Karotte",
        "Knackiges orangefarbenes Gemüse.",
        "Nutzer A",
        metadata={"category": ["Gemüse", "Lebensmittel"]},
    )

    payload = fake_client.points[point_id].payload
    assert payload["title"] == "Karotte"
    assert payload["description"] == "Knackiges orangefarbenes Gemüse."
    assert payload["category"] == ["Gemüse", "Lebensmittel"]
    assert manager._embedding_text("Karotte", "Knackiges orangefarbenes Gemüse.") == (
        "Title: Karotte | Description: Knackiges orangefarbenes Gemüse."
    )
