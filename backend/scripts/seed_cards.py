"""
Seed tarot card data from JSON files into database
"""
import sys
import json
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy.exc import IntegrityError
from src.core.database import SessionLocal
from src.models import Card, ArcanaType, Suit
from src.core.logging import get_logger

logger = get_logger(__name__)


def load_json_data(file_path: Path) -> List[Dict]:
    """
    Load card data from JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        List of card dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} cards from {file_path.name}")
            return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []


def validate_card_data(card_data: Dict) -> bool:
    """
    Validate card data before insertion

    Args:
        card_data: Card dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        'name', 'name_ko', 'arcana_type',
        'keywords_upright', 'keywords_reversed',
        'meaning_upright', 'meaning_reversed'
    ]

    for field in required_fields:
        if field not in card_data:
            logger.error(f"Missing required field '{field}' in card: {card_data.get('name', 'Unknown')}")
            return False

    # Validate arcana_type
    if card_data['arcana_type'] not in ['major', 'minor']:
        logger.error(f"Invalid arcana_type: {card_data['arcana_type']}")
        return False

    # Validate suit for minor arcana
    if card_data['arcana_type'] == 'minor':
        if not card_data.get('suit'):
            logger.error(f"Minor arcana card missing suit: {card_data['name']}")
            return False
        if card_data['suit'] not in ['wands', 'cups', 'swords', 'pentacles']:
            logger.error(f"Invalid suit: {card_data['suit']}")
            return False

    # Validate keywords are lists
    if not isinstance(card_data['keywords_upright'], list):
        logger.error(f"keywords_upright must be a list: {card_data['name']}")
        return False
    if not isinstance(card_data['keywords_reversed'], list):
        logger.error(f"keywords_reversed must be a list: {card_data['name']}")
        return False

    return True


def create_card_from_data(card_data: Dict, db) -> Card:
    """
    Create Card model instance from dictionary

    Args:
        card_data: Card dictionary
        db: Database session

    Returns:
        Card model instance
    """
    # Convert string values to enums
    arcana_type = ArcanaType.MAJOR if card_data['arcana_type'] == 'major' else ArcanaType.MINOR

    suit = None
    if card_data.get('suit'):
        suit_map = {
            'wands': Suit.WANDS,
            'cups': Suit.CUPS,
            'swords': Suit.SWORDS,
            'pentacles': Suit.PENTACLES
        }
        suit = suit_map.get(card_data['suit'])

    # Create card instance
    card = Card(
        name=card_data['name'],
        name_ko=card_data['name_ko'],
        number=card_data.get('number'),
        arcana_type=arcana_type,
        suit=suit,
        keywords_upright=card_data['keywords_upright'],
        keywords_reversed=card_data['keywords_reversed'],
        meaning_upright=card_data['meaning_upright'],
        meaning_reversed=card_data['meaning_reversed'],
        description=card_data.get('description'),
        symbolism=card_data.get('symbolism'),
        image_url=card_data.get('image_url')
    )

    return card


def seed_cards_from_file(file_path: Path, db) -> int:
    """
    Seed cards from a single JSON file

    Args:
        file_path: Path to JSON file
        db: Database session

    Returns:
        Number of cards successfully seeded
    """
    cards_data = load_json_data(file_path)
    if not cards_data:
        return 0

    seeded_count = 0
    skipped_count = 0

    for card_data in cards_data:
        # Validate data
        if not validate_card_data(card_data):
            skipped_count += 1
            continue

        try:
            # Check if card already exists
            existing = db.query(Card).filter(Card.name == card_data['name']).first()
            if existing:
                logger.info(f"Card already exists, skipping: {card_data['name']}")
                skipped_count += 1
                continue

            # Create and add card
            card = create_card_from_data(card_data, db)
            db.add(card)
            db.commit()
            seeded_count += 1
            logger.debug(f"Seeded card: {card.name} ({card.name_ko})")

        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error for card {card_data['name']}: {e}")
            skipped_count += 1
        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding card {card_data['name']}: {e}")
            skipped_count += 1

    logger.info(f"File {file_path.name}: {seeded_count} seeded, {skipped_count} skipped")
    return seeded_count


def seed_all_cards(clear_existing: bool = False):
    """
    Seed all tarot cards from JSON files

    Args:
        clear_existing: If True, clear existing cards before seeding
    """
    logger.info("=" * 60)
    logger.info("Starting Tarot Card Seeding Process")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # Clear existing cards if requested
        if clear_existing:
            count = db.query(Card).count()
            if count > 0:
                logger.warning(f"Clearing {count} existing cards from database...")
                db.query(Card).delete()
                db.commit()
                logger.info("Existing cards cleared")

        # Define card data files
        data_dir = Path(__file__).resolve().parents[1] / "data" / "cards"
        card_files = [
            data_dir / "major_arcana.json",
            data_dir / "minor_wands.json",
            data_dir / "minor_cups.json",
            data_dir / "minor_swords.json",
            data_dir / "minor_pentacles.json"
        ]

        # Seed cards from each file
        total_seeded = 0
        for file_path in card_files:
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                continue

            count = seed_cards_from_file(file_path, db)
            total_seeded += count

        # Final summary
        total_cards = db.query(Card).count()
        logger.info("=" * 60)
        logger.info(f"Seeding Complete!")
        logger.info(f"  - Cards seeded in this run: {total_seeded}")
        logger.info(f"  - Total cards in database: {total_cards}")
        logger.info("=" * 60)

        # Show breakdown by arcana type
        major_count = db.query(Card).filter(Card.arcana_type == ArcanaType.MAJOR).count()
        minor_count = db.query(Card).filter(Card.arcana_type == ArcanaType.MINOR).count()
        logger.info(f"Breakdown:")
        logger.info(f"  - Major Arcana: {major_count} cards")
        logger.info(f"  - Minor Arcana: {minor_count} cards")

        # Show breakdown by suit
        for suit in [Suit.WANDS, Suit.CUPS, Suit.SWORDS, Suit.PENTACLES]:
            suit_count = db.query(Card).filter(Card.suit == suit).count()
            logger.info(f"    - {suit.value.title()}: {suit_count} cards")

        return total_seeded

    except Exception as e:
        logger.error(f"Fatal error during seeding: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed tarot card data into database")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing cards before seeding"
    )
    args = parser.parse_args()

    # Run seeding
    seeded = seed_all_cards(clear_existing=args.clear)

    # Exit with appropriate code
    sys.exit(0 if seeded > 0 else 1)
