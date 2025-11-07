"""
RAG (Retrieval-Augmented Generation) System for Tarot Readings

This package provides a complete RAG pipeline for enriching Tarot readings
with deep knowledge from the knowledge base.

Main Components:
    - EmbeddingModel: Multilingual sentence embeddings
    - VectorStore: ChromaDB-based semantic search
    - KnowledgeBase: JSON-based knowledge management
    - Retriever: High-level retrieval operations
    - ContextEnricher: Context aggregation for prompts

Usage:
    from src.ai.rag import ContextEnricher

    enricher = ContextEnricher()
    context = enricher.enrich_prompt_context(
        cards=[{"id": 0, "is_reversed": False}],
        spread_type="one_card",
        question="What should I focus on today?"
    )
"""

from .embeddings import EmbeddingModel, get_embedding_model
from .vector_store import VectorStore
from .knowledge_base import KnowledgeBase
from .retriever import Retriever
from .context_enricher import ContextEnricher

__all__ = [
    "EmbeddingModel",
    "get_embedding_model",
    "VectorStore",
    "KnowledgeBase",
    "Retriever",
    "ContextEnricher",
]
