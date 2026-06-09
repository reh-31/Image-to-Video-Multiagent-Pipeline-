"""Chroma-backed vector store with sentence-transformers embeddings.

Two collections:
  • "style_guides"  — FotoOwl visual style descriptions
  • "remotion_api"  — Remotion API code reference snippets
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_chroma_client = None
_embedding_model = None


def _get_chroma():
    """Return (or lazily create) the persistent Chroma client."""
    global _chroma_client
    if _chroma_client is None:
        import chromadb

        _chroma_client = chromadb.PersistentClient(path="./.cache/chroma")
        logger.info("Chroma client initialised at ./.cache/chroma")
    return _chroma_client


def _get_embedding_function():
    """Return a chromadb-compatible embedding function backed by sentence-transformers."""
    global _embedding_model
    if _embedding_model is None:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        _embedding_model = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        logger.info("Embedding model all-MiniLM-L6-v2 loaded.")
    return _embedding_model


def get_collection(collection_name: str):
    """Get or create a named Chroma collection with sentence-transformer embeddings."""
    client = _get_chroma()
    ef = _get_embedding_function()
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef,
    )


def retrieve(query: str, collection_name: str, n_results: int = 3) -> list[str]:
    """Retrieve the top-*n_results* documents most similar to *query*.

    Returns a list of document strings (the raw text that was seeded).
    Falls back to an empty list if the collection is empty or if
    chromadb / sentence-transformers are not installed.
    """
    try:
        collection = get_collection(collection_name)
        count = collection.count()
        if count == 0:
            logger.warning(
                "Collection '%s' is empty — returning no RAG context.", collection_name
            )
            return []

        actual_n = min(n_results, count)
        results = collection.query(query_texts=[query], n_results=actual_n)
        docs: list[str] = results.get("documents", [[]])[0]
        return docs
    except Exception as exc:
        logger.warning("RAG retrieval failed for '%s': %s", collection_name, exc)
        return []


def upsert_documents(
    collection_name: str,
    documents: list[str],
    ids: Optional[list[str]] = None,
) -> None:
    """Insert or replace *documents* into *collection_name*.

    If *ids* is not provided, sequential integer IDs are generated.
    """
    collection = get_collection(collection_name)
    if ids is None:
        ids = [str(i) for i in range(len(documents))]
    collection.upsert(documents=documents, ids=ids)
    logger.info(
        "Upserted %d documents into collection '%s'.", len(documents), collection_name
    )
