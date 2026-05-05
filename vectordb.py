"""Chroma client + Ollama embedding function factory (cached singleton)."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

import chromadb
import httpx
import ollama

PROJECT_ROOT = Path(__file__).parent
VECTORDB_DIR = PROJECT_ROOT / "vectordb"
COLLECTION_NAME = "knowledge_base"

_client = None
_collection = None


class OllamaEmbedding:
    """Custom Ollama embedding function with long timeout + keep_alive.

    The stock chromadb.OllamaEmbeddingFunction uses a ~60s httpx timeout,
    which isn't enough when Ollama has to swap a cold embedding model in
    while gemma4:e4b is resident. We raise the timeout and set keep_alive
    so the embedding model stays hot for subsequent calls in the session.
    """

    def __init__(self, model_name: str, url: str, keep_alive: str = "30m"):
        self.model_name = model_name
        self.url = url
        self.keep_alive = keep_alive
        self._client = ollama.Client(
            host=url,
            timeout=httpx.Timeout(300.0, connect=10.0),
        )

    def name(self) -> str:  # chromadb EmbeddingFunction protocol
        return f"ollama-{self.model_name}"

    def __call__(self, input: list[str]) -> list[list[float]]:
        # ollama.Client.embed handles batching natively in newer versions
        resp = self._client.embed(
            model=self.model_name,
            input=input,
            keep_alive=self.keep_alive,
        )
        return resp["embeddings"]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "OllamaEmbedding":
        return OllamaEmbedding(
            model_name=config["model_name"],
            url=config["url"],
            keep_alive=config.get("keep_alive", "30m"),
        )

    def get_config(self) -> dict[str, Any]:
        return {"model_name": self.model_name, "url": self.url, "keep_alive": self.keep_alive}

    def default_space(self) -> str:
        return "cosine"

    def is_legacy(self) -> bool:
        return False


def _embedding_fn() -> OllamaEmbedding:
    return OllamaEmbedding(
        model_name=os.getenv("EMBED_MODEL", "nomic-embed-text"),
        url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
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
