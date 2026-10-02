from __future__ import annotations

import uuid

import pytest
from qdrant_client import QdrantClient

from config import AppConfig
from database import VectorDBManager


class VectorValue(list[float]):
    def tolist(self) -> list[float]:
        return list(self)


class IntegrationEncoder:
    def encode(self, value, batch_size=32):
        if isinstance(value, str):
            return VectorValue([float(len(value)), 1.0, 0.0])
        return [VectorValue([float(len(text)), 1.0, 0.0]) for text in value]


@pytest.mark.integration
def test_qdrant_isolation_on_separate_collection() -> None:
    collection = f"space_objects_test_{uuid.uuid4().hex[:12]}"
    client = QdrantClient(host="localhost", port=6333, timeout=10)
    try:
        client.get_collections()
    except Exception as exc:
        pytest.skip(f"Qdrant nicht erreichbar: {exc}")

    manager = VectorDBManager(
        config=AppConfig(collection_name=collection, embedding_dimension=3),
        client=client,
        encoder=IntegrationEncoder(),
    )
    try:
        manager.create_collection()
        point_a = manager.insert_data("A", "Eintrag A", "Nutzer A")
        point_b = manager.insert_data("B", "Eintrag B", "Nutzer B")
        assert [item["id"] for item in manager.get_all_for_user("Nutzer A")] == [point_a]
        assert [item["id"] for item in manager.get_all_for_user("Nutzer B")] == [point_b]
        assert manager.count_for_user("Nutzer A") == 1
    finally:
        client.delete_collection(collection)
