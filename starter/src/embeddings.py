"""Real embedding provider adapters (Gemini and OpenRouter) implementing the Embedder contract.

Compliant with Day 06 rules: no silent fallback to random/mock vectors.
Includes robust retry and backoff handling for Gemini Free Tier rate limits (100 RPM).
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Protocol
import httpx
from dotenv import load_dotenv

# Load environment from project root or starter
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class GeminiEmbedder:
    """Embedding adapter using Google Gemini API (gemini-embedding-001 or text-embedding-004)."""

    def __init__(
        self,
        model_name: str = "gemini-embedding-001",
        dimensions: int = 768,
        api_key: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.target_dimensions = dimensions
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY chua duoc thiet lap trong .env hoac bien moi truong. "
                "Vui long them GEMINI_API_KEY vao file .env."
            )
        self.dimensions = dimensions
        self._test_connection()

    def _test_connection(self) -> None:
        """Verify API key and dimension compatibility on initialization."""
        try:
            test_vec = self.embed_query("kiem tra ket noi")
            self.dimensions = len(test_vec)
        except RuntimeError as e:
            if "not found" in str(e).lower() and self.model_name != "gemini-embedding-001":
                self.model_name = "gemini-embedding-001"
                test_vec = self.embed_query("kiem tra ket noi")
                self.dimensions = len(test_vec)
            else:
                raise

    def embed_query(self, question: str) -> list[float]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": question}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": self.target_dimensions,
        }
        with httpx.Client(timeout=30.0) as client:
            for attempt in range(5):
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["embedding"]["values"]
                elif resp.status_code == 429:
                    wait_time = 15.0
                    m = re.search(r"(\d+(\.\d+)?)s", resp.text)
                    if m:
                        wait_time = float(m.group(1)) + 2.0
                    print(f"    [Rate limit 429] Cho {wait_time:.1f}s de hoi phuc quota...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(
                        f"Gemini API embed_query loi (HTTP {resp.status_code}): {resp.text}"
                    )
            raise RuntimeError("Gemini API embed_query vuot qua so lan thu lai do rate limit.")

    def embed_documents(self, texts: list[str], batch_size: int = 40) -> list[list[float]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:batchEmbedContents?key={self.api_key}"
        all_embeddings: list[list[float]] = []

        with httpx.Client(timeout=60.0) as client:
            total_batches = (len(texts) + batch_size - 1) // batch_size
            for b_idx in range(total_batches):
                i = b_idx * batch_size
                batch = texts[i : i + batch_size]
                requests = [
                    {
                        "model": f"models/{self.model_name}",
                        "content": {"parts": [{"text": t}]},
                        "taskType": "RETRIEVAL_DOCUMENT",
                        "outputDimensionality": self.target_dimensions,
                    }
                    for t in batch
                ]

                # Retry loop on 429
                success = False
                for attempt in range(6):
                    resp = client.post(url, json={"requests": requests})
                    if resp.status_code == 200:
                        data = resp.json()
                        embeddings = [item["values"] for item in data.get("embeddings", [])]
                        if len(embeddings) != len(batch):
                            raise RuntimeError(
                                f"So luong vector tra ve ({len(embeddings)}) khac input ({len(batch)})"
                            )
                        all_embeddings.extend(embeddings)
                        print(f"    -> Da embed batch {b_idx+1}/{total_batches} ({len(all_embeddings)}/{len(texts)} chunks)")
                        success = True
                        # Brief pause between batches to respect free tier RPM
                        time.sleep(1.0)
                        break
                    elif resp.status_code == 429:
                        wait_time = 15.0
                        m = re.search(r"(\d+(\.\d+)?)s", resp.text)
                        if m:
                            wait_time = float(m.group(1)) + 3.0
                        print(f"    [Gemini Quota 429] Cho {wait_time:.1f}s de hoi phuc quota truoc khi tiep tuc...")
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(
                            f"Gemini API batchEmbedContents loi (HTTP {resp.status_code}): {resp.text}"
                        )

                if not success:
                    raise RuntimeError(f"Loi: Batch {b_idx+1} khong the hoan tat sau nhieu lan retry.")

        return all_embeddings


class OpenRouterEmbedder:
    """Embedding adapter using OpenRouter / OpenAI compatible API."""

    def __init__(
        self,
        model_name: str = "openai/text-embedding-3-small",
        api_key: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY chua duoc thiet lap trong .env hoac bien moi truong. "
                "Vui long them OPENROUTER_API_KEY vao file .env."
            )
        self.dimensions = 1536
        self._test_connection()

    def _test_connection(self) -> None:
        test_vec = self.embed_query("connection test")
        self.dimensions = len(test_vec)

    def embed_query(self, question: str) -> list[float]:
        res = self.embed_documents([question])
        return res[0]

    def embed_documents(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        url = "https://openrouter.ai/api/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "Day06 Data Ingestion Lab",
        }
        all_embeddings: list[list[float]] = []

        with httpx.Client(timeout=60.0) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                payload = {"model": self.model_name, "input": batch}
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"OpenRouter API embeddings loi (HTTP {resp.status_code}): {resp.text}"
                    )
                data = resp.json()
                items = sorted(data["data"], key=lambda x: x["index"])
                embeddings = [item["embedding"] for item in items]
                all_embeddings.extend(embeddings)

        return all_embeddings


def get_embedder(provider: str | None = None, model_name: str | None = None) -> Embedder:
    """Factory to construct embedder based on environment and parameters."""
    provider = provider or os.getenv("EMBEDDING_PROVIDER", "").strip().lower()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if provider == "gemini" or (not provider and gemini_key):
        model = model_name or os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
        return GeminiEmbedder(model_name=model, dimensions=768)
    elif provider == "openrouter" or (not provider and openrouter_key):
        model = model_name or os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
        return OpenRouterEmbedder(model_name=model)
    else:
        raise ValueError(
            "Chua cau hinh API key phu hop! Vui long them GEMINI_API_KEY hoac OPENROUTER_API_KEY vao file .env."
        )
