"""
Test Card model and database operations
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect
from src.core.database import SessionLocal, engine
from src.models import Card, ArcanaType, Suit


def test_table_exists():
    """Test that cards table exists in database"""
    print("=" * 60)
    print("Testing Table Existence")
    print("=" * 60)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "cards" in tables:
        print("✅ 'cards' table exists")

        # Get columns
        columns = inspector.get_columns("cards")
        print(f"\nTable has {len(columns)} columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

        # Get indexes
        indexes = inspector.get_indexes("cards")
        print(f"\nTable has {len(indexes)} indexes:")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['column_names']}")

        return True
    else:
        print(f"❌ 'cards' table not found. Available tables: {tables}")
        return False


def test_create_card():
    """Test creating a card"""
    print("\n" + "=" * 60)
    print("Testing Card Creation")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Create a test card (The Fool)
        card = Card(
            name="The Fool",
            name_ko="바보",
            number=0,
            arcana_type=ArcanaType.MAJOR,
            suit=None,
            keywords_upright=["new beginnings", "innocence", "spontaneity", "free spirit"],
            keywords_reversed=["recklessness", "risk-taking", "naivety"],
            meaning_upright="The Fool represents new beginnings, having faith in the future, being inexperienced, not knowing what to expect, having beginner's luck, improvisation and believing in the universe.",
            meaning_reversed="The Fool reversed represents recklessness, taking unnecessary risks, being too naive, and failing to learn from past mistakes.",
            description="A young person stands at the edge of a cliff, looking upward with a carefree expression.",
            symbolism="The white rose represents purity, the small dog represents loyalty, and the cliff edge represents the unknown.",
            image_url="/images/cards/00-the-fool.jpg"
        )

        db.add(card)
        db.commit()
        db.refresh(card)

        print(f"✅ Card created successfully!")
        print(f"   ID: {card.id}")
        print(f"   Name: {card.name} ({card.name_ko})")
        print(f"   Arcana: {card.arcana_type.value}")
        print(f"   Keywords (upright): {', '.join(card.keywords_upright)}")

        return card.id

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating card: {e}")
        return None
    finally:
        db.close()


def test_read_card(card_id: int):
    """Test reading a card"""
    print("\n" + "=" * 60)
    print("Testing Card Retrieval")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Read by ID
        card = db.query(Card).filter(Card.id == card_id).first()

        if card:
            print(f"✅ Card retrieved successfully!")
            print(f"   {card}")
            print(f"   Created: {card.created_at}")
            print(f"   Updated: {card.updated_at}")
            return True
        else:
            print(f"❌ Card not found with ID: {card_id}")
            return False

    except Exception as e:
        print(f"❌ Error reading card: {e}")
        return False
    finally:
        db.close()


def test_query_filters():
    """Test querying with filters"""
    print("\n" + "=" * 60)
    print("Testing Query Filters")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Count all cards
        total = db.query(Card).count()
        print(f"Total cards in database: {total}")

        # Query by arcana type
        major_arcana = db.query(Card).filter(Card.arcana_type == ArcanaType.MAJOR).count()
        print(f"Major Arcana cards: {major_arcana}")

        # Query by name
        fool = db.query(Card).filter(Card.name == "The Fool").first()
        if fool:
            print(f"✅ Found 'The Fool' by name query")

        return True

    except Exception as e:
        print(f"❌ Error querying cards: {e}")
        return False
    finally:
        db.close()


def test_to_dict():
    """Test to_dict method"""
    print("\n" + "=" * 60)
    print("Testing to_dict() Method")
    print("=" * 60)

    db = SessionLocal()

    try:
        card = db.query(Card).first()
        if card:
            card_dict = card.to_dict()
            print("✅ to_dict() conversion successful!")
            print("\nCard as dictionary:")
            import json
            print(json.dumps(card_dict, indent=2, ensure_ascii=False))
            return True
        else:
            print("❌ No cards found to test")
            return False

    except Exception as e:
        print(f"❌ Error converting to dict: {e}")
        return False
    finally:
        db.close()


def test_create_minor_arcana():
    """Test creating a Minor Arcana card"""
    print("\n" + "=" * 60)
    print("Testing Minor Arcana Card Creation")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Create Ace of Wands
        card = Card(
            name="Ace of Wands",
            name_ko="완드 에이스",
            number=1,
            arcana_type=ArcanaType.MINOR,
            suit=Suit.WANDS,
            keywords_upright=["inspiration", "new opportunities", "growth", "potential"],
            keywords_reversed=["lack of direction", "delays", "setbacks"],
            meaning_upright="The Ace of Wands represents inspiration, new opportunities, and creative potential.",
            meaning_reversed="The Ace of Wands reversed represents delays, lack of direction, and missed opportunities.",
            description="A hand emerging from a cloud holds a wooden wand.",
            symbolism="The wand represents creativity and potential, the hand represents divine guidance.",
            image_url="/images/cards/wands-01.jpg"
        )

        db.add(card)
        db.commit()
        db.refresh(card)

        print(f"✅ Minor Arcana card created successfully!")
        print(f"   Name: {card.name} ({card.name_ko})")
        print(f"   Arcana: {card.arcana_type.value}")
        print(f"   Suit: {card.suit.value}")

        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating Minor Arcana card: {e}")
        return False
    finally:
        db.close()


def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 60)
    print("Cleaning Up Test Data")
    print("=" * 60)

    db = SessionLocal()

    try:
        deleted_count = db.query(Card).delete()
        db.commit()
        print(f"✅ Deleted {deleted_count} test card(s)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error cleaning up: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Starting Card Model Tests\n")

    all_passed = True

    # Run tests
    all_passed &= test_table_exists()

    card_id = test_create_card()
    if card_id:
        all_passed &= test_read_card(card_id)
        all_passed &= test_query_filters()
        all_passed &= test_to_dict()

    all_passed &= test_create_minor_arcana()

    # Clean up
    cleanup_test_data()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    print("\n")

    sys.exit(0 if all_passed else 1)
