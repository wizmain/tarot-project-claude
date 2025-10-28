"""
Generate placeholder SVG images for tarot cards
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from src.core.database import SessionLocal
from src.core.logging import get_logger

logger = get_logger(__name__)


def generate_svg_card(card_name: str, card_name_ko: str, suit: str = None, arcana_type: str = 'major') -> str:
    """
    Generate a beautiful SVG placeholder for a tarot card

    Args:
        card_name: English card name
        card_name_ko: Korean card name
        suit: Card suit (wands, cups, swords, pentacles) or None for major arcana
        arcana_type: 'major' or 'minor'

    Returns:
        SVG string
    """
    # Color schemes based on suit/arcana
    if arcana_type == 'major':
        gradient_start = '#7c3aed'  # purple-600
        gradient_end = '#4c1d95'    # purple-900
        symbol = '✨'
        symbol_color = '#fbbf24'    # amber-400
    elif suit == 'wands':
        gradient_start = '#f59e0b'  # amber-500
        gradient_end = '#b45309'    # amber-700
        symbol = '🔥'
        symbol_color = '#fef3c7'    # amber-100
    elif suit == 'cups':
        gradient_start = '#3b82f6'  # blue-500
        gradient_end = '#1e3a8a'    # blue-900
        symbol = '💧'
        symbol_color = '#dbeafe'    # blue-100
    elif suit == 'swords':
        gradient_start = '#6b7280'  # gray-500
        gradient_end = '#1f2937'    # gray-800
        symbol = '⚔️'
        symbol_color = '#f3f4f6'    # gray-100
    elif suit == 'pentacles':
        gradient_start = '#10b981'  # emerald-500
        gradient_end = '#065f46'    # emerald-800
        symbol = '⭐'
        symbol_color = '#d1fae5'    # emerald-100
    else:
        gradient_start = '#8b5cf6'  # violet-500
        gradient_end = '#5b21b6'    # violet-800
        symbol = '✦'
        symbol_color = '#ede9fe'    # violet-100

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="600" viewBox="0 0 400 600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cardGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{gradient_start};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{gradient_end};stop-opacity:1" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.3"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="400" height="600" fill="url(#cardGradient)" rx="8"/>

  <!-- Border decoration -->
  <rect x="20" y="20" width="360" height="560" fill="none" stroke="{symbol_color}" stroke-width="3" rx="4" opacity="0.5"/>
  <rect x="30" y="30" width="340" height="540" fill="none" stroke="{symbol_color}" stroke-width="2" rx="4" opacity="0.3"/>

  <!-- Symbol at top -->
  <text x="200" y="120" font-size="80" text-anchor="middle" opacity="0.8">{symbol}</text>

  <!-- Card name in English -->
  <text x="200" y="300" font-size="28" font-weight="bold" text-anchor="middle" fill="{symbol_color}" font-family="Georgia, serif">
    {card_name}
  </text>

  <!-- Card name in Korean -->
  <text x="200" y="340" font-size="32" font-weight="bold" text-anchor="middle" fill="{symbol_color}" font-family="Arial, sans-serif">
    {card_name_ko}
  </text>

  <!-- Symbol at bottom -->
  <text x="200" y="520" font-size="60" text-anchor="middle" opacity="0.6">{symbol}</text>

  <!-- Decorative corner elements -->
  <circle cx="60" cy="60" r="8" fill="{symbol_color}" opacity="0.4"/>
  <circle cx="340" cy="60" r="8" fill="{symbol_color}" opacity="0.4"/>
  <circle cx="60" cy="540" r="8" fill="{symbol_color}" opacity="0.4"/>
  <circle cx="340" cy="540" r="8" fill="{symbol_color}" opacity="0.4"/>
</svg>'''

    return svg


def main():
    """Generate all card images"""
    db = SessionLocal()

    try:
        # Get all cards from database
        query = text("""
            SELECT name, name_ko, suit, arcana_type, image_url
            FROM cards
            ORDER BY id
        """)
        result = db.execute(query)
        cards = result.fetchall()

        logger.info(f"Found {len(cards)} cards in database")

        # Output directory
        output_dir = Path(__file__).resolve().parents[2] / 'frontend' / 'public' / 'images' / 'cards'
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Output directory: {output_dir}")

        # Generate SVG for each card
        generated_count = 0
        for card in cards:
            name, name_ko, suit, arcana_type, image_url = card

            # Extract filename from image_url
            filename = Path(image_url).name
            # Change extension to svg
            svg_filename = filename.replace('.jpg', '.svg').replace('.png', '.svg')
            output_path = output_dir / svg_filename

            # Generate SVG
            svg_content = generate_svg_card(
                card_name=name,
                card_name_ko=name_ko,
                suit=suit,
                arcana_type=arcana_type
            )

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)

            generated_count += 1
            if generated_count % 10 == 0:
                logger.info(f"Generated {generated_count}/{len(cards)} images...")

        logger.info(f"✅ Successfully generated {generated_count} card images!")
        logger.info(f"📁 Location: {output_dir}")

    except Exception as e:
        logger.error(f"Error generating images: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
