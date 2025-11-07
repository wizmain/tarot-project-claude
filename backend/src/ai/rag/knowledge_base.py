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
                "name_ko": "Korean",
                "deep_meaning": "...",
                "symbolism": {...},
                "upright_themes": [...],
                ...
            }
        """
        try:
            # Determine if major or minor arcana
            # NOTE: Current knowledge base only has 21 Major Arcana cards (0-20)
            # Standard tarot has 22 (0-21), so we handle both cases
            if 0 <= card_id <= 20:
                arcana_type = "major_arcana"
                # Format: 00_the_fool.json, 01_the_magician.json, etc.
                file_pattern = f"{card_id:02d}_*.json"
                card_dir = self.knowledge_base_path / "cards" / arcana_type
                card_dir.mkdir(parents=True, exist_ok=True)

                # Find matching file
                matching_files = list(card_dir.glob(file_pattern))

            elif card_id == 21:
                # Card 21 doesn't exist in current knowledge base
                # Map it to card 20 (The World) temporarily
                logger.warning(f"Card ID 21 not found, using card 20 (The World) as fallback")
                return self.load_card_knowledge(20)

            else:
                # Minor Arcana: IDs 22-77 (56 cards total)
                # 22-35: Wands (Ace through King = 14 cards)
                # 36-49: Cups
                # 50-63: Swords
                # 64-77: Pentacles
                arcana_type = "minor_arcana"

                # Determine suit and rank
                minor_id = card_id - 22  # 0-55
                suit_index = minor_id // 14  # 0=wands, 1=cups, 2=swords, 3=pentacles
                rank_in_suit = (minor_id % 14) + 1  # 1-14

                suits = ["wands", "cups", "swords", "pentacles"]
                suit = suits[suit_index] if suit_index < len(suits) else None

                if not suit:
                    logger.warning(f"Invalid card ID: {card_id} (out of range)")
                    return None

                # Format: 01_ace_of_wands.json, 02_two_of_wands.json, etc.
                file_pattern = f"{rank_in_suit:02d}_*_of_{suit}.json"
                card_dir = self.knowledge_base_path / "cards" / arcana_type / suit
                card_dir.mkdir(parents=True, exist_ok=True)

                # Find matching file
                matching_files = list(card_dir.glob(file_pattern))

            if not matching_files:
                logger.warning(f"Card knowledge not found for ID: {card_id} (pattern: {file_pattern})")
                return None

            card_file = matching_files[0]

            with open(card_file, 'r', encoding='utf-8') as f:
                card_data = json.load(f)

            logger.debug(f"Loaded card knowledge: {card_data.get('name', 'Unknown')}")
            return card_data

        except Exception as e:
            logger.error(f"Failed to load card knowledge for ID {card_id}: {e}")
            return None

    def load_spread_knowledge(self, spread_type: str) -> Optional[Dict[str, Any]]:
        """
        Load knowledge for a specific spread type

        Args:
            spread_type: Spread identifier (e.g., "one_card", "three_card_past_present_future")

        Returns:
            Dictionary containing spread knowledge, or None if not found

        Example structure:
            {
                "id": "one_card",
                "name": "One Card Reading",
                "description": "...",
                "positions": [...],
                "interpretation_guide": "...",
                ...
            }
        """
        try:
            spread_file = self.knowledge_base_path / "spreads" / f"{spread_type}.json"

            if not spread_file.exists():
                logger.warning(f"Spread knowledge not found: {spread_type}")
                return None

            with open(spread_file, 'r', encoding='utf-8') as f:
                spread_data = json.load(f)

            logger.debug(f"Loaded spread knowledge: {spread_data.get('name', 'Unknown')}")
            return spread_data

        except Exception as e:
            logger.error(f"Failed to load spread knowledge for {spread_type}: {e}")
            return None

    def load_combination_knowledge(
        self,
        combination_file: str = "major_pairs.json"
    ) -> Optional[Dict[str, Any]]:
        """
        Load card combination patterns

        Args:
            combination_file: Name of the combination file

        Returns:
            Dictionary containing card combination patterns, or None if not found

        Example structure:
            {
                "combinations": [
                    {
                        "card_ids": [0, 8],
                        "cards": ["The Fool", "Strength"],
                        "meaning": "...",
                        "meaning_ko": "..."
                    },
                    ...
                ]
            }
        """
        try:
            combo_file = self.knowledge_base_path / "combinations" / combination_file

            if not combo_file.exists():
                logger.warning(f"Combination knowledge not found: {combination_file}")
                return None

            with open(combo_file, 'r', encoding='utf-8') as f:
                combo_data = json.load(f)

            logger.debug(f"Loaded {len(combo_data.get('combinations', []))} card combinations")
            return combo_data

        except Exception as e:
            logger.error(f"Failed to load combination knowledge: {e}")
            return None

    def load_category_knowledge(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Load category-specific interpretation guides

        Args:
            category: Reading category (e.g., "career", "love", "finance")

        Returns:
            Dictionary containing category-specific knowledge, or None if not found

        Example structure:
            {
                "category": "career",
                "name_ko": "KoreanKorean",
                "interpretation_focus": [...],
                "card_specific_meanings": {
                    "0": {
                        "context": "Career",
                        "upright": "...",
                        "reversed": "..."
                    },
                    ...
                }
            }
        """
        try:
            category_file = self.knowledge_base_path / "categories" / f"{category}.json"

            if not category_file.exists():
                logger.warning(f"Category knowledge not found: {category}")
                return None

            with open(category_file, 'r', encoding='utf-8') as f:
                category_data = json.load(f)

            logger.debug(f"Loaded category knowledge: {category}")
            return category_data

        except Exception as e:
            logger.error(f"Failed to load category knowledge for {category}: {e}")
            return None

    def get_all_cards(self) -> List[Dict[str, Any]]:
        """
        Load all available card knowledge

        Returns:
            List of all card data dictionaries
        """
        all_cards = []

        try:
            cards_dir = self.knowledge_base_path / "cards"

            # Load major arcana
            major_dir = cards_dir / "major_arcana"
            if major_dir.exists():
                for card_file in sorted(major_dir.glob("*.json")):
                    with open(card_file, 'r', encoding='utf-8') as f:
                        all_cards.append(json.load(f))

            # Load minor arcana
            minor_dir = cards_dir / "minor_arcana"
            if minor_dir.exists():
                for card_file in sorted(minor_dir.glob("*.json")):
                    with open(card_file, 'r', encoding='utf-8') as f:
                        all_cards.append(json.load(f))

            logger.info(f"Loaded {len(all_cards)} cards from knowledge base")
            return all_cards

        except Exception as e:
            logger.error(f"Failed to load all cards: {e}")
            return []

    def get_all_spreads(self) -> List[Dict[str, Any]]:
        """
        Load all available spread patterns

        Returns:
            List of all spread data dictionaries
        """
        all_spreads = []

        try:
            spreads_dir = self.knowledge_base_path / "spreads"

            if spreads_dir.exists():
                for spread_file in spreads_dir.glob("*.json"):
                    with open(spread_file, 'r', encoding='utf-8') as f:
                        all_spreads.append(json.load(f))

            logger.info(f"Loaded {len(all_spreads)} spreads from knowledge base")
            return all_spreads

        except Exception as e:
            logger.error(f"Failed to load all spreads: {e}")
            return []
