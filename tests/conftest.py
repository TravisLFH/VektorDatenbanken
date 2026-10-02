from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class FakePoint:
    id: str
    payload: dict[str, Any]
    vector: list[float]


class FakeEncoder:
    def encode(self, value: str | list[str], batch_size: int = 32) -> Any:
        values = [value] if isinstance(value, str) else value
        vectors = [[float(len(text)), 1.0, 0.0] for text in values]
        return vectors[0] if isinstance(value, str) else vectors

    def get_embedding_dimension(self) -> int:
        return 3


class FakeClient:
    def __init__(self) -> None:
        self.points: dict[str, FakePoint] = {}

    def _matches(self, point: FakePoint, query_filter: Any) -> bool:
        for condition in query_filter.must:
            if hasattr(condition, "key") and condition.key == "user_id":
                if point.payload.get("user_id") != condition.match.value:
                    return False
            if hasattr(condition, "has_id") and str(point.id) not in {
                str(point_id) for point_id in condition.has_id
            }:
                return False
        return True

    def upsert(self, collection_name: str, points: list[Any]) -> None:
        for point in points:
            self.points[str(point.id)] = FakePoint(
                id=str(point.id), payload=point.payload, vector=point.vector
            )

    def scroll(self, collection_name: str, scroll_filter: Any, limit: int, **kwargs: Any) -> tuple[list[FakePoint], None]:
        matches = [point for point in self.points.values() if self._matches(point, scroll_filter)]
        return matches[:limit], None

    def delete(self, collection_name: str, points_selector: Any) -> None:
        query_filter = points_selector.filter
        for point_id, point in list(self.points.items()):
            if self._matches(point, query_filter):
                del self.points[point_id]


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()
