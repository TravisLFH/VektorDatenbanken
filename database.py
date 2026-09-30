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

import uuid
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer


class VectorDBManager:
    """Manages the connection to Qdrant and all CRUD/search operations
    for the 'space_objects' collection."""

    COLLECTION_NAME = "space_objects"
    # The model maps text to a 384-dimensional embedding vector.
    EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSION = 384

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        # Loading the transformer is deferred until a vector is actually needed.
        self.encoder: Optional[SentenceTransformer] = None
        self.vector_size = self.EMBEDDING_DIMENSION

    def _get_encoder(self) -> SentenceTransformer:
        """Loads the embedding model on first use and reuses it afterwards."""
        if self.encoder is None:
            self.encoder = SentenceTransformer(self.EMBEDDING_MODEL_NAME)
        return self.encoder

    def create_collection(self, recreate: bool = False) -> None:
        """Initializes the 'space_objects' collection.

        Args:
            recreate: If True, drops and recreates the collection (useful
                for resetting the demo to a clean state).
        """
        exists = self.client.collection_exists(self.COLLECTION_NAME)
        if exists and not recreate:
            return
        if exists and recreate:
            self.client.delete_collection(self.COLLECTION_NAME)

        # `recreate_collection()` was removed in newer qdrant-client versions;
        # `create_collection()` is now the single entry point for this.
        self.client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def _embed(self, text: str) -> List[float]:
        """Converts a text string into a vector embedding."""
        return self._get_encoder().encode(text).tolist()

    def embed_text(self, text: str) -> List[float]:
        """Creates the embedding used for a query or a stored description."""
        return self._embed(text)

    def insert_data(self, name: str, description: str, user_id: str) -> str:
        """Embeds a description and stores it as a new point in Qdrant.

        Returns:
            The generated UUID of the newly created point.
        """
        point_id = str(uuid.uuid4())
        vector = self._embed(description)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "name": name,
                        "description": description,
                        "user_id": user_id,
                    },
                )
            ],
        )
        return point_id

    def update_data(self, point_id: str, name: str, description: str, user_id: str) -> None:
        """Overwrites an existing point's vector and payload.

        Since the description text changes, the embedding is recomputed
        so that search results stay semantically accurate.
        """
        vector = self._embed(description)

        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "name": name,
                        "description": description,
                        "user_id": user_id,
                    },
                )
            ],
        )

    def search_data(self, query_text: str, user_id: str, limit: int = 5) -> List[dict]:
        """Performs a semantic vector search restricted to a single user.

        The `user_id` filter is applied server-side by Qdrant, guaranteeing
        that one user can never see another user's data - this is the
        core of the multi-tenant isolation demo.
        """
        query_vector = self._embed(query_text)

        user_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        )

        # `search()` was removed in newer qdrant-client versions in favor
        # of the unified `query_points()` API.
        response = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            query_filter=user_filter,
            limit=limit,
            with_payload=True,
            with_vectors=True,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "name": hit.payload.get("name"),
                "description": hit.payload.get("description"),
                "user_id": hit.payload.get("user_id"),
                "vector": hit.vector,
            }
            for hit in response.points
        ]

    def get_all_for_user(self, user_id: str) -> List[dict]:
        """Fetches every point (vector + payload) belonging to one user.

        Used for the 2D PCA visualization so it only ever shows data the
        active user is allowed to see - again enforcing isolation.
        """
        user_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        )

        points, _ = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=user_filter,
            limit=1000,
            with_payload=True,
            with_vectors=True,
        )

        return [
            {
                "id": p.id,
                "vector": p.vector,
                "name": p.payload.get("name"),
                "description": p.payload.get("description"),
            }
            for p in points
        ]

    def delete_data(self, point_id: str) -> None:
        """Removes a single point by its UUID."""
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.PointIdsList(points=[point_id]),
        )

    def delete_user_data(self, user_id: str) -> None:
        """Removes every point belonging to a single user.

        Uses a `FilterSelector` so the deletion happens server-side and can
        never accidentally touch another user's data.
        """
        user_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        )
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.FilterSelector(filter=user_filter),
        )

    def delete_all_data(self) -> None:
        """Wipes the entire collection (all users) and recreates it empty."""
        self.create_collection(recreate=True)

    def count_all(self) -> int:
        """Returns the total number of points across all users."""
        return self.client.count(self.COLLECTION_NAME, exact=True).count

    def seed_demo_data(self, user_id: str) -> int:
        """Inserts a curated set of mixed sample data for one user.

        Useful for quickly populating the demo so the search and the PCA
        cluster visualization have enough data to be meaningful.

        Returns:
            The number of objects inserted.
        """
        sample_objects = [
            ("Anna Weber", "Eine erfahrene Ärztin, die Patientinnen untersucht, Diagnosen stellt und in einer Klinik arbeitet."),
            ("Mehmet Kaya", "Ein engagierter Softwareentwickler, der Python programmiert und moderne Webanwendungen baut."),
            ("Sophie Schneider", "Eine geduldige Lehrerin, die Mathematik erklärt und Jugendliche auf Prüfungen vorbereitet."),
            ("Lukas Fischer", "Ein kreativer Fotograf, der Porträts und Landschaften aufnimmt und Bilder professionell bearbeitet."),
            ("Clara Hoffmann", "Eine Architektin, die nachhaltige Gebäude entwirft und Baupläne für neue Wohnungen erstellt."),
            ("Jonas Becker", "Ein gelernter Schreiner, der individuelle Holzmöbel baut, repariert und sorgfältig bearbeitet."),
            ("Mia Wagner", "Eine Studentin der Informatik, die Algorithmen lernt, an einer Hausarbeit schreibt und gerne programmiert."),
            ("Noah Klein", "Ein Maschinenbaustudent, der technische Konstruktionen entwickelt und sich auf Robotik spezialisiert."),
            ("Lea Neumann", "Eine Studentin der Psychologie, die für Klausuren lernt und sich mit menschlichem Verhalten beschäftigt."),
            ("Paul Richter", "Ein Student der Betriebswirtschaft, der Vorlesungen besucht, Statistiken auswertet und in einer Lerngruppe arbeitet."),
            ("Emilia Wolf", "Eine Studentin der Biologie, die im Labor forscht und sich für Ökosysteme und Tiere interessiert."),
            ("Finn Hartmann", "Ein Architekturstudent, der Modelle baut, Grundrisse zeichnet und Ideen für moderne Gebäude entwickelt."),
            ("Holzschreibtisch", "Ein stabiler Schreibtisch aus hellem Holz mit Schubladen, an dem man arbeiten oder lernen kann."),
            ("Bürostuhl", "Ein ergonomischer Drehstuhl mit verstellbarer Rückenlehne und Rollen für einen komfortablen Arbeitsplatz."),
            ("Stehlampe", "Eine hohe Lampe für das Wohnzimmer, die einen Raum gleichmäßig beleuchtet und warmes Licht spendet."),
            ("Bücherregal", "Ein breites Regal aus Holz mit mehreren Fächern zur Aufbewahrung von Büchern, Ordnern und Dekoration."),
            ("Kaffeemaschine", "Ein elektrisches Küchengerät, das schnell frischen Kaffee für mehrere Personen zubereitet."),
            ("Fahrrad", "Ein leichtes Verkehrsmittel mit zwei Rädern, das sich für den täglichen Weg und sportliche Touren eignet."),
        ]

        for name, description in sample_objects:
            self.insert_data(name, description, user_id)

        return len(sample_objects)
