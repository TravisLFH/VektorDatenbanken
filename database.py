"""
database.py
------------
Encapsulates all interaction with the Qdrant vector database for the
"Planets and Space Objects" demo.

Core concepts demonstrated here:
- Turning free-text descriptions into dense vector embeddings (semantic meaning).
- Storing vectors together with a JSON "payload" (metadata) in Qdrant.
- Filtering search results by `user_id` to simulate strict multi-tenant
  data isolation (a common real-world requirement for vector databases).
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, List, Mapping, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from config import CONFIG, AppConfig
from errors import (
    CollectionConfigurationError,
    DatabaseUnavailableError,
    EmbeddingModelError,
    EntryNotFoundError,
)
from validation import validate_point_id, validate_search_limit, validate_text, validate_user_id

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


class VectorDBManager:
    """Manages the connection to Qdrant and all CRUD/search operations
    for the 'space_objects' collection."""

    COLLECTION_NAME = "space_objects"
    # The model maps text to a 384-dimensional embedding vector.
    EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION = 384

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        config: AppConfig | None = None,
        client: QdrantClient | None = None,
        encoder: Optional["SentenceTransformer"] = None,
    ):
        self.config = config or CONFIG
        self.collection_name = self.config.collection_name
        client_options = {
            "host": host or self.config.qdrant_host,
            "port": port or self.config.qdrant_port,
            "api_key": self.config.qdrant_api_key,
            "timeout": self.config.qdrant_timeout,
        }
        self.client = client or QdrantClient(**client_options)
        # The encoder is loaded on demand and can be warmed up by the app entrypoint.
        self.encoder: Optional["SentenceTransformer"] = encoder
        self.vector_size = self.config.embedding_dimension

    def _get_encoder(self) -> "SentenceTransformer":
        """Loads the embedding model on first use and reuses it afterwards."""
        if self.encoder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self.encoder = SentenceTransformer(
                    self.config.embedding_model,
                    local_files_only=False,
                )
            except Exception as exc:
                logger.exception("Embedding-Modell konnte nicht geladen werden.")
                raise EmbeddingModelError(
                    "Das Embedding-Modell konnte weder aus dem lokalen Hugging-Face-Cache "
                    "geladen noch aus dem Internet heruntergeladen werden."
                ) from exc
        return self.encoder

    def warm_up_model(self) -> None:
        """Lädt das gecachte Embedding-Modell vor der ersten Nutzeraktion."""
        self._get_encoder()

    def create_collection(self, recreate: bool = False) -> None:
        """Initializes the 'space_objects' collection.

        Args:
            recreate: If True, drops and recreates the collection (useful
                for resetting the demo to a clean state).
        """
        try:
            exists = self.client.collection_exists(self.collection_name)
            if exists and recreate:
                self.client.delete_collection(self.collection_name)
                exists = False

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
            else:
                self._verify_collection_configuration()

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="category",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except CollectionConfigurationError:
            raise
        except Exception as exc:
            logger.exception("Qdrant-Collection konnte nicht initialisiert werden.")
            raise DatabaseUnavailableError(
                "Qdrant ist nicht erreichbar oder die Collection konnte nicht initialisiert werden."
            ) from exc

    def _verify_collection_configuration(self) -> None:
        """Bricht bei inkompatiblen Vektorparametern statt stiller Migration ab."""
        info = self.client.get_collection(self.collection_name)
        vectors = info.config.params.vectors
        if not isinstance(vectors, models.VectorParams):
            raise CollectionConfigurationError(
                "Die bestehende Collection verwendet eine nicht unterstützte Vektorkonfiguration."
            )
        if vectors.size != self.vector_size or vectors.distance != models.Distance.COSINE:
            raise CollectionConfigurationError(
                f"Die Collection '{self.collection_name}' hat inkompatible Vektoreinstellungen "
                f"(erwartet: {self.vector_size}D/COSINE)."
            )

    def health_check(self) -> bool:
        """Prüft Erreichbarkeit und Kompatibilität der konfigurierten Collection."""
        try:
            self.create_collection()
            return True
        except (DatabaseUnavailableError, CollectionConfigurationError):
            return False

    def _embed(self, text: str) -> List[float]:
        """Converts a text string into a vector embedding."""
        try:
            return self._get_encoder().encode(text).tolist()
        except EmbeddingModelError:
            raise
        except Exception as exc:
            logger.exception("Embedding konnte nicht erzeugt werden.")
            raise EmbeddingModelError("Der Text konnte nicht eingebettet werden.") from exc

    def _embed_many(self, texts: List[str]) -> List[List[float]]:
        """Erzeugt Embeddings batchweise für größere Schreiboperationen."""
        try:
            vectors = self._get_encoder().encode(texts, batch_size=32)
            return vectors.tolist()
        except EmbeddingModelError:
            raise
        except Exception as exc:
            logger.exception("Batch-Embedding konnte nicht erzeugt werden.")
            raise EmbeddingModelError("Die Texte konnten nicht eingebettet werden.") from exc

    @staticmethod
    def _embedding_text(title: str, description: str) -> str:
        """Builds the explicit text representation used for embeddings."""
        return f"Title: {title} | Description: {description}"

    def embed_text(self, text: str) -> List[float]:
        """Creates the embedding used for a query or a stored description."""
        return self._embed(text)

    @staticmethod
    def build_user_filter(user_id: str) -> models.Filter:
        """Erzeugt den einheitlichen serverseitigen Mandantenfilter."""
        user_id = validate_user_id(user_id)
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        )

    def _build_owned_point_filter(self, point_id: str, user_id: str) -> models.Filter:
        """Kombiniert UUID und Nutzerfilter für Einzelaktionen."""
        point_id = validate_point_id(point_id)
        return models.Filter(
            must=[
                *self.build_user_filter(user_id).must,
                models.HasIdCondition(has_id=[point_id]),
            ]
        )

    def _ensure_owned(self, point_id: str, user_id: str) -> str:
        """Prüft Besitz per Qdrant-Filter vor einer Einzeländerung."""
        point_id = validate_point_id(point_id)
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=self._build_owned_point_filter(point_id, user_id),
            limit=1,
            with_payload=False,
            with_vectors=False,
        )
        if not points:
            raise EntryNotFoundError(
                "Der Eintrag existiert nicht mehr oder gehört nicht zum aktiven Nutzer."
            )
        return point_id

    def _build_payload(
        self,
        title: str,
        description: str,
        user_id: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Combines user metadata with the fields required by the application."""
        payload = dict(metadata or {})
        payload.update(
            {
                "title": title,
                "name": title,
                "description": description,
                "user_id": user_id,
            }
        )
        return payload

    def insert_data(
        self,
        name: str,
        description: str,
        user_id: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Embeds a description and stores it as a new point in Qdrant.

        Returns:
            The generated UUID of the newly created point.
        """
        name = validate_text(name, "Titel", self.config.max_name_length)
        description = validate_text(
            description, "Beschreibung", self.config.max_description_length
        )
        user_id = validate_user_id(user_id)
        point_id = str(uuid.uuid4())
        vector = self._embed(self._embedding_text(name, description))

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=self._build_payload(name, description, user_id, metadata),
                )
            ],
        )
        return point_id

    def update_data(
        self,
        point_id: str,
        name: str,
        description: str,
        user_id: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Overwrites an existing point's vector and payload.

        Since the description text changes, the embedding is recomputed
        so that search results stay semantically accurate.
        """
        point_id = validate_point_id(point_id)
        name = validate_text(name, "Titel", self.config.max_name_length)
        description = validate_text(
            description, "Beschreibung", self.config.max_description_length
        )
        user_id = validate_user_id(user_id)
        point_id = self._ensure_owned(point_id, user_id)
        vector = self._embed(self._embedding_text(name, description))

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=self._build_payload(name, description, user_id, metadata),
                )
            ],
        )

    def search_data(
        self,
        query_text: str,
        user_id: str,
        limit: int = 5,
        include_vectors: bool = False,
        category: str | tuple[str, ...] | list[str] | None = None,
    ) -> List[dict]:
        """Performs a semantic vector search restricted to a single user.

        The `user_id` filter is applied server-side by Qdrant, guaranteeing
        that one user can never see another user's data - this is the
        core of the multi-tenant isolation demo.
        """
        query_text = validate_text(query_text, "Suchtext", self.config.max_description_length)
        user_id = validate_user_id(user_id)
        limit = validate_search_limit(limit, self.config.max_search_limit)
        categories = []
        if isinstance(category, str):
            categories = [validate_text(category, "Kategorie", 80)]
        elif category is not None:
            categories = [validate_text(value, "Kategorie", 80) for value in category]
        query_vector = self._embed(query_text)

        filter_conditions = list(self.build_user_filter(user_id).must)
        search_filter = models.Filter(
            must=filter_conditions,
            should=[
                models.FieldCondition(
                    key="category",
                    match=models.MatchValue(value=value),
                )
                for value in categories
            ] or None,
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=include_vectors,
        )

        return [
            self._point_to_result(hit, include_vectors=include_vectors, score=hit.score)
            for hit in response.points
        ]

    def get_all_for_user(self, user_id: str, include_vectors: bool = False) -> List[dict]:
        """Lädt alle Punkte eines Nutzers seitenweise.

        Used for the 2D PCA visualization so it only ever shows data the
        active user is allowed to see - again enforcing isolation.
        """
        user_filter = self.build_user_filter(user_id)

        points = []
        offset = None
        while True:
            scroll_kwargs = {
                "collection_name": self.collection_name,
                "scroll_filter": user_filter,
                "limit": 256,
                "with_payload": True,
                "with_vectors": include_vectors,
            }
            if offset is not None:
                scroll_kwargs["offset"] = offset
            page, next_offset = self.client.scroll(**scroll_kwargs)
            points.extend(page)
            if next_offset is None or not page:
                break
            offset = next_offset

        return [self._point_to_result(p, include_vectors=include_vectors) for p in points]

    @staticmethod
    def _point_to_result(point: object, include_vectors: bool, score: float | None = None) -> dict:
        """Normalisiert Punkte mit fehlenden Payload-Feldern zu sicheren Defaults."""
        payload = dict(getattr(point, "payload", None) or {})
        result = {
            **payload,
            "id": str(getattr(point, "id", "")),
            "score": score,
            "vector": getattr(point, "vector", None) if include_vectors else None,
            "qdrant_payload": payload,
            "title": payload.get("title", payload.get("name", "Ohne Titel")),
            "description": payload.get("description", "Keine Beschreibung"),
            "user_id": payload.get("user_id"),
        }
        result["name"] = result["title"]
        return result

    def delete_data(self, point_id: str, user_id: str) -> None:
        """Removes one point only when UUID and Nutzer gemeinsam match."""
        point_id = self._ensure_owned(point_id, user_id)
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=self._build_owned_point_filter(point_id, user_id)
            ),
        )

    def delete_user_data(self, user_id: str) -> None:
        """Removes every point belonging to a single user.

        Uses a `FilterSelector` so the deletion happens server-side and can
        never accidentally touch another user's data.
        """
        user_filter = self.build_user_filter(user_id)
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=user_filter),
        )

    def reindex_user_data(self, user_id: str) -> int:
        """Recreates vectors for existing records after embedding changes."""
        user_id = validate_user_id(user_id)
        objects = self.get_all_for_user(user_id)
        if not objects:
            return 0
        valid_objects = []
        texts = []
        for obj in objects:
            try:
                name = validate_text(
                    obj.get("name", "Unbenannt"), "Name", self.config.max_name_length
                )
                description = validate_text(
                    obj.get("description", ""),
                    "Beschreibung",
                    self.config.max_description_length,
                )
            except Exception:
                logger.warning("Fehlerhafter Punkt %s beim Reindex übersprungen.", obj.get("id"))
                continue
            metadata = {
                key: value
                for key, value in obj.items()
                if key not in {"id", "score", "vector", "title", "name", "description", "user_id", "tags"}
            }
            valid_objects.append((obj, name, description, metadata))
            texts.append(self._embedding_text(name, description))
        if not valid_objects:
            return 0
        vectors = self._embed_many(texts)
        points = [
            models.PointStruct(
                id=validate_point_id(obj["id"]),
                vector=vector,
                payload=self._build_payload(name, description, user_id, metadata),
            )
            for (obj, name, description, metadata), vector in zip(valid_objects, vectors, strict=True)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def delete_all_data(self) -> None:
        """Wipes the entire collection (all users) and recreates it empty."""
        self.create_collection(recreate=True)

    def count_all(self) -> int:
        """Returns the total number of points across all users."""
        return self.client.count(self.collection_name, exact=True).count

    def count_for_user(self, user_id: str) -> int:
        """Zählt ausschließlich Punkte des validierten aktiven Nutzers."""
        return self.client.count(
            self.collection_name,
            count_filter=self.build_user_filter(user_id),
            exact=True,
        ).count

    def seed_demo_data(self, user_id: str) -> int:
        """Inserts the curated sample data from ``demo_daten.md`` for one user.

        Useful for quickly populating the demo so the search and the PCA
        cluster visualization have enough data to be meaningful.

        Returns:
            The number of objects inserted.
        """
        from demo_data import iter_demo_entries_with_metadata

        sample_objects = iter_demo_entries_with_metadata()

        user_id = validate_user_id(user_id)
        existing = {
            (obj.get("name", obj.get("title")), obj["description"])
            for obj in self.get_all_for_user(user_id)
        }
        pending = [
            (name, description, metadata)
            for name, description, metadata in sample_objects
            if (name, description) not in existing
        ]
        if not pending:
            return 0

        vectors = self._embed_many(
            [self._embedding_text(name, description) for name, description, _metadata in pending]
        )
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=self._build_payload(name, description, user_id, metadata),
            )
            for (name, description, metadata), vector in zip(pending, vectors, strict=True)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        return len(points)
