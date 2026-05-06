"""Chroma client + Google Gemini embedding function (cached singleton).

Uses Google's gemini-embedding-001 (768-dim) via the langchain-google-genai
package. GOOGLE_API_KEY must be set in the environment.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings

PROJECT_ROOT = Path(__file__).parent
VECTORDB_DIR = PROJECT_ROOT / "vectordb"
COLLECTION_NAME = "knowledge_base"

_client = None
_collection = None


class GeminiEmbedding:
    """Chroma-compatible adapter around langchain-google-genai's embeddings.

    Implements the chromadb EmbeddingFunction protocol:
      __call__, name, get_config, build_from_config, default_space, is_legacy.
    """

    def __init__(self, model_name: str = "gemini-embedding-001"):
        self.model_name = model_name
        # langchain-google-genai picks up GOOGLE_API_KEY from env automatically.
        self._inner = GoogleGenerativeAIEmbeddings(model=model_name)

    def name(self) -> str:  # chromadb protocol
        return f"gemini-{self.model_name.split('/')[-1]}"

    def __call__(self, input: list[str]) -> list[list[float]]:
        # embed_documents handles batching/retries internally.
        return self._inner.embed_documents(list(input))

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "GeminiEmbedding":
        return GeminiEmbedding(model_name=config.get("model_name", "gemini-embedding-001"))

    def get_config(self) -> dict[str, Any]:
        return {"model_name": self.model_name}

    def default_space(self) -> str:
        return "cosine"

    def is_legacy(self) -> bool:
        return False


def _embedding_fn() -> GeminiEmbedding:
    return GeminiEmbedding(
        model_name=os.getenv("EMBED_MODEL", "gemini-embedding-001"),
    )


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        VECTORDB_DIR.mkdir(exist_ok=True)
        _client = chromadb.PersistentClient(path=str(VECTORDB_DIR))
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_embedding_fn(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection
