"""Seeds the Chroma vector store on startup.  Idempotent — skips seeding
if collections already contain documents.
"""
from __future__ import annotations

import logging

from rag.vector_store import get_collection, upsert_documents

logger = logging.getLogger(__name__)


def seed_if_empty() -> None:
    """Seed style_guides and remotion_api collections if they are empty."""
    _seed_style_guides()
    _seed_remotion_api()


def _seed_style_guides() -> None:
    """Seed the style_guides collection unless it already has documents."""
    from rag.seed_data.style_guides import STYLE_GUIDE_DOCS

    collection = get_collection("style_guides")
    if collection.count() > 0:
        logger.info("style_guides already seeded (%d docs). Skipping.", collection.count())
        return

    ids = [f"style_{i}" for i in range(len(STYLE_GUIDE_DOCS))]
    upsert_documents("style_guides", STYLE_GUIDE_DOCS, ids)
    print(f"[RAG] Seeded style_guides with {len(STYLE_GUIDE_DOCS)} documents.")


def _seed_remotion_api() -> None:
    """Seed the remotion_api collection unless it already has documents."""
    from rag.seed_data.remotion_api import REMOTION_API_DOCS

    collection = get_collection("remotion_api")
    if collection.count() > 0:
        logger.info("remotion_api already seeded (%d docs). Skipping.", collection.count())
        return

    ids = [f"remotion_{i}" for i in range(len(REMOTION_API_DOCS))]
    upsert_documents("remotion_api", REMOTION_API_DOCS, ids)
    print(f"[RAG] Seeded remotion_api with {len(REMOTION_API_DOCS)} documents.")
