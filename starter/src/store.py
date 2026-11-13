"""Vector store implementation using Qdrant (Local Persistent Storage).

Complies with Day 06 specifications:
- Persistent disk storage
- Cosine distance metric
- Idempotent upsert with deduplication and replacement
- Structured metadata filtering
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from .models import Chunk


class QdrantVectorStore:
    def __init__(self, storage_path: str = "./results/qdrant_data", dimensions: int = 768) -> None:
        self.storage_path = str(Path(storage_path).resolve())
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        self.dimensions = dimensions
        # Initialize local persistent Qdrant client
        self.client = QdrantClient(path=self.storage_path)

    def _get_collection_name(self, strategy: str) -> str:
        # Standardize strategy collection name (e.g., "strategy_a", "strategy_b", "strategy_c")
        clean_name = strategy.lower().replace("-", "_").replace(" ", "_")
        return f"day06_{clean_name}"

    def create_schema(self, strategy: str) -> None:
        """Ensure collection exists with configured vector dimensions and Cosine metric."""
        col_name = self._get_collection_name(strategy)
        collections = [c.name for c in self.client.get_collections().collections]
        if col_name not in collections:
            self.client.create_collection(
                collection_name=col_name,
                vectors_config=qmodels.VectorParams(
                    size=self.dimensions,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Idempotently insert or update chunks with vectors and payload."""
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Chunks count ({len(chunks)}) does not match vectors count ({len(vectors)})"
            )

        col_name = self._get_collection_name(strategy)
        self.create_schema(strategy)

        # Batch upsert points with deterministic UUIDs based on chunk_id
        points: list[qmodels.PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.dimensions:
                raise ValueError(
                    f"Vector dimension {len(vector)} does not match store dimension {self.dimensions}"
                )

            # Deterministic UUIDv5 ensures idempotency on repeated ingestion
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "source": chunk.source,
                "page": chunk.page,
                "text": chunk.text,
                **chunk.metadata,
            }

            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        # Batch upload to avoid memory pressure
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=col_name, points=batch)

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search top-k nearest vectors using cosine similarity with optional metadata filter."""
        col_name = self._get_collection_name(strategy)

        query_filter: qmodels.Filter | None = None
        if filters:
            conditions: list[qmodels.FieldCondition] = []
            for key, val in filters.items():
                conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=val),
                    )
                )
            if conditions:
                query_filter = qmodels.Filter(must=conditions)

        # In qdrant-client >= 1.10, query_points or search can be used
        results = self.client.query_points(
            collection_name=col_name,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        ).points

        hits: list[dict[str, Any]] = []
        for r in results:
            payload = r.payload or {}
            hits.append({
                "id": str(r.id),
                "chunk_id": payload.get("chunk_id", ""),
                "score": float(r.score),
                "text": payload.get("text", ""),
                "page": payload.get("page", 0),
                "source": payload.get("source", ""),
                "metadata": payload,
            })

        return hits
