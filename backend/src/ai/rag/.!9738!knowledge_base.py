"""
Knowledge Base Management for RAG System

This module handles loading and managing Tarot knowledge from JSON files,
including card meanings, spread patterns, combinations, and category-specific guides.

Classes:
    KnowledgeBase: Manager for loading Tarot knowledge data
"""
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Knowledge base manager for Tarot reading data

    Loads and provides access to card meanings, spread patterns,
    card combinations, and category-specific interpretation guides.

    Attributes:
        knowledge_base_path: Path to the knowledge base directory
    """

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialize the knowledge base

        Args:
            knowledge_base_path: Path to knowledge base directory
                                (default: backend/data/knowledge_base/)
        """
        if knowledge_base_path is None:
            backend_root = Path(__file__).parent.parent.parent.parent
            knowledge_base_path = str(backend_root / "data" / "knowledge_base")

        self.knowledge_base_path = Path(knowledge_base_path)

        if not self.knowledge_base_path.exists():
            logger.warning(f"Knowledge base path does not exist: {self.knowledge_base_path}")
            self.knowledge_base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"KnowledgeBase initialized at: {self.knowledge_base_path}")

    def load_card_knowledge(self, card_id: int) -> Optional[Dict[str, Any]]:
        """
        Load knowledge for a specific card

        Args:
            card_id: Card ID (0-77, where 0-21 are major arcana)

        Returns:
            Dictionary containing card knowledge, or None if not found

        Example structure:
            {
                "id": 0,
                "name": "The Fool",
