"""
Test script for card knowledge loader

Verifies that all 78 tarot cards can be loaded correctly from the knowledge base.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import get_logger
from src.ai.rag.knowledge_base import KnowledgeBase

logger = get_logger(__name__)


def test_card_loader():
    """Test loading all 78 tarot cards"""
    print("\n" + "=" * 70)
    print("Card Knowledge Loader Test")
    print("=" * 70 + "\n")

    kb = KnowledgeBase()
    print(f"Knowledge base path: {kb.knowledge_base_path}\n")

    # Test cases
    test_cards = [
        (0, "The Fool", "Major Arcana"),
        (10, "Justice", "Major Arcana"),
        (20, "The World", "Major Arcana"),
        (22, "Ace of Wands", "Minor Arcana - Wands"),
        (35, "King of Wands", "Minor Arcana - Wands"),
        (36, "Ace of Cups", "Minor Arcana - Cups"),
        (49, "King of Cups", "Minor Arcana - Cups"),
        (50, "Ace of Swords", "Minor Arcana - Swords"),
        (63, "King of Swords", "Minor Arcana - Swords"),
        (64, "Ace of Pentacles", "Minor Arcana - Pentacles"),
        (77, "King of Pentacles", "Minor Arcana - Pentacles"),
    ]

    print("Testing specific cards:\n")
    success_count = 0
    fail_count = 0

    for card_id, expected_name, category in test_cards:
        knowledge = kb.load_card_knowledge(card_id)
        if knowledge:
            actual_name = knowledge.get('name', 'Unknown')
            print(f"  ✓ ID {card_id:2d}: {actual_name:30s} ({category})")
            success_count += 1
        else:
            print(f"  ✗ ID {card_id:2d}: FAILED - Expected {expected_name:30s} ({category})")
            fail_count += 1

    print(f"\n{'='*70}")
    print(f"Results: {success_count} success, {fail_count} failed")

    # Test all 78 cards
    print(f"\n{'='*70}")
    print("Testing all 78 cards:\n")

    all_success = 0
    all_fail = 0

    for card_id in range(78):
        knowledge = kb.load_card_knowledge(card_id)
        if knowledge:
            all_success += 1
        else:
            all_fail += 1
            print(f"  ✗ Missing: Card ID {card_id}")

    print(f"\n{'='*70}")
    print(f"Total: {all_success}/78 cards loaded successfully")
    if all_fail > 0:
        print(f"⚠️  {all_fail} cards failed to load")
    else:
        print("✅ All 78 cards loaded successfully!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_card_loader()
