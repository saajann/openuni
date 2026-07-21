import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models


class QdrantStore:
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "demo_collection",
        vector_size: int = 768,
    ):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the collection if it does not exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            print(f"Creating Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size, distance=models.Distance.COSINE
                ),
            )
        else:
            print(f"Qdrant collection '{self.collection_name}' already exists.")

    def delete_university_data(self, university_slug: str):
        """Deletes all existing points for the given university to avoid duplicates on re-run."""
        print(f"Deleting existing data for university '{university_slug}' in Qdrant...")
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="university_slug",
                            match=models.MatchValue(value=university_slug),
                        ),
                    ],
                )
            ),
        )

    def upsert_points(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        """Upserts a batch of vectors and their payloads into Qdrant."""
        if not vectors or len(vectors) != len(payloads):
            return

        points = [
            models.PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
            for vector, payload in zip(vectors, payloads)
        ]

        self.client.upsert(collection_name=self.collection_name, points=points)
