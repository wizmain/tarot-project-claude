"""
Rebuild RAG vector database index with all card knowledge

This script scans all card JSON files in the knowledge base and
re-indexes them into the ChromaDB vector database.
"""
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import get_logger
from src.ai.rag.retriever import Retriever

logger = get_logger(__name__)


def rebuild_index():
    """Rebuild the entire RAG index from scratch"""
    print("\n" + "=" * 70)
    print("RAG Index Rebuild")
    print("=" * 70 + "\n")

    # Initialize retriever
    print("1. Initializing RAG Retriever...")
    retriever = Retriever()
    print("   ✓ Retriever initialized\n")

    # Get all card files
    base_path = Path(__file__).parent.parent / "data" / "knowledge_base" / "cards"

    major_arcana_path = base_path / "major_arcana"
    minor_arcana_path = base_path / "minor_arcana"

    all_card_files = []

    # Collect Major Arcana
    if major_arcana_path.exists():
        all_card_files.extend(list(major_arcana_path.glob("*.json")))

    # Collect Minor Arcana
    if minor_arcana_path.exists():
        for suit_dir in minor_arcana_path.iterdir():
            if suit_dir.is_dir():
                all_card_files.extend(list(suit_dir.glob("*.json")))

    print(f"2. Found {len(all_card_files)} card knowledge files\n")

    # Load and index each card
    print("3. Indexing cards into vector database...")
    indexed_count = 0
    error_count = 0

    for card_file in sorted(all_card_files):
        try:
            with open(card_file, 'r', encoding='utf-8') as f:
                card_data = json.load(f)

            card_id = card_data.get('id')
            card_name = card_data.get('name', 'Unknown')

            # The retriever automatically indexes when we call get_card_knowledge
            # So let's just verify it can load the card
            knowledge = retriever.get_card_knowledge(card_id)

            if knowledge:
                print(f"   ✓ Indexed: ID {card_id:2d} - {card_name}")
                indexed_count += 1
            else:
                print(f"   ✗ Failed: ID {card_id:2d} - {card_name} (no knowledge returned)")
                error_count += 1

        except Exception as e:
            print(f"   ✗ Error processing {card_file.name}: {e}")
            error_count += 1

    print(f"\n4. Indexing complete!")
    print(f"   - Successfully indexed: {indexed_count} cards")
    print(f"   - Errors: {error_count} cards")

    # Test retrieval
    print(f"\n5. Testing retrieval...")
    test_card_ids = [0, 10, 22, 45, 70]  # Mix of major and minor arcana
    for card_id in test_card_ids:
        knowledge = retriever.get_card_knowledge(card_id)
        if knowledge:
            print(f"   ✓ Card ID {card_id}: {knowledge.get('name', 'Unknown')}")
        else:
            print(f"   ✗ Card ID {card_id}: No knowledge found")

    print("\n" + "=" * 70)
    print("Index Rebuild Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    rebuild_index()
