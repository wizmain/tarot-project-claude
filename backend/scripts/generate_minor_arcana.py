"""
Generate Minor Arcana knowledge base files

This script generates all 56 Minor Arcana cards (14 cards × 4 suits)
"""
import json
from pathlib import Path

# Minor Arcana structure
SUITS = {
    "wands": {
        "element": "Fire",
        "themes": "action, ambition, creativity, passion, willpower",
        "korean": "완드"
    },
    "cups": {
        "element": "Water",
        "themes": "emotions, relationships, feelings, intuition",
        "korean": "컵"
    },
    "swords": {
        "element": "Air",
        "themes": "thoughts, communication, conflict, intellect",
        "korean": "검"
    },
    "pentacles": {
        "element": "Earth",
        "themes": "material, money, career, physical world",
        "korean": "펜타클"
    }
}

RANKS = [
    ("ace", 1, "Ace", "에이스"),
    ("two", 2, "Two", "2"),
    ("three", 3, "Three", "3"),
    ("four", 4, "Four", "4"),
    ("five", 5, "Five", "5"),
    ("six", 6, "Six", "6"),
    ("seven", 7, "Seven", "7"),
    ("eight", 8, "Eight", "8"),
    ("nine", 9, "Nine", "9"),
    ("ten", 10, "Ten", "10"),
    ("page", 11, "Page", "페이지"),
    ("knight", 12, "Knight", "나이트"),
    ("queen", 13, "Queen", "퀸"),
    ("king", 14, "King", "킹")
]

# Generic meanings for ranks (to be customized per suit)
RANK_MEANINGS = {
    1: "new beginnings, opportunities, potential",
    2: "balance, partnership, duality",
    3: "collaboration, groups, growth",
    4: "foundation, stability, structure",
    5: "conflict, change, challenge",
    6: "harmony, communication, cooperation",
    7: "assessment, reflection, perseverance",
    8: "movement, action, progress",
    9: "achievement, near completion",
    10: "completion, fulfillment, end of cycle",
    11: "new ideas, enthusiasm, messages",
    12: "swift action, courage, pursuit",
    13: "nurturing, intuitive, caring authority",
    14: "mastery, control, leadership"
}

def generate_minor_card(suit, suit_data, rank_name, rank_num, rank_display, rank_ko, card_id):
    """Generate a single minor arcana card"""

    card_name = f"{rank_display} of {suit.capitalize()}"
    card_name_ko = f"{suit_data['korean']}의 {rank_ko}"

    # Generate meanings based on suit and rank
    suit_theme = suit_data['themes']
    rank_theme = RANK_MEANINGS[rank_num]

    deep_meaning = f"The {card_name} combines the {suit_data['element']} element's focus on {suit_theme} with the energy of {rank_theme}. "

    if rank_num == 1:
        deep_meaning += f"As an Ace, this card represents the pure, undiluted potential of {suit}. It's a gift from the universe, an opportunity to begin something new in the realm of {suit_theme}."
    elif rank_num <= 10:
        deep_meaning += f"This numbered card shows the progression of {suit} energy through concrete life experiences and situations."
    else:  # Court cards
        court_meanings = {
            11: f"The Page brings messages and new learning in {suit_theme}. Youthful energy and enthusiasm.",
            12: f"The Knight takes action, pursuing {suit_theme} with determination and speed.",
            13: f"The Queen embodies mastery of {suit_theme} through nurturing and intuitive wisdom.",
            14: f"The King represents full mastery and authoritative command of {suit_theme}."
        }
        deep_meaning += court_meanings[rank_num]

    card_json = {
        "id": card_id,
        "name": card_name,
        "name_ko": card_name_ko,
        "arcana_type": "minor",
        "suit": suit,
        "rank": rank_display.lower(),
        "number": rank_num,
        "deep_meaning": deep_meaning,
        "deep_meaning_ko": f"{card_name_ko}는 {suit_theme}의 에너지를 나타냅니다.",
        "symbolism": {
            suit: f"{suit_data['element']} element energy",
            rank_display.lower(): rank_theme
        },
        "upright_themes": [
            suit_theme.split(", ")[0],
            rank_theme.split(", ")[0],
            "progress",
            "development"
        ],
        "reversed_themes": [
            f"blocked {suit_theme.split(', ')[0]}",
            f"resistance to {rank_theme.split(', ')[0]}",
            "delays"
        ],
        "upright_extended": deep_meaning,
        "reversed_extended": f"When reversed, {card_name} suggests challenges or blockages in {suit_theme}. The natural flow is interrupted.",
        "element": suit_data["element"],
        "numerology": f"Number {rank_num}: {rank_theme}",
        "related_cards": [],
        "questions_to_ask": [
            f"How is the {suit_data['element']} energy of {suit} manifesting in my life?",
            f"What does this card teach me about {suit_theme}?"
        ]
    }

    return card_json

# Main generation
base_path = Path("/Users/wizmain/Documents/workspace/tarot-project-claude/backend/data/knowledge_base/cards/minor_arcana")
created_count = 0

# Calculate card IDs
card_id = 22  # Start after Major Arcana (0-21)

print("Generating Minor Arcana cards...")
print("=" * 70)

for suit, suit_data in SUITS.items():
    suit_path = base_path / suit
    suit_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{suit.upper()} ({suit_data['element']})")
    print("-" * 50)

    for rank_name, rank_num, rank_display, rank_ko in RANKS:
        # Skip cards we already have
        filename = f"{rank_num:02d}_{rank_name}_of_{suit}.json"
        filepath = suit_path / filename

        if filepath.exists():
            print(f"  ⊙ Exists: {filename}")
            card_id += 1
            continue

        card_json = generate_minor_card(suit, suit_data, rank_name, rank_num, rank_display, rank_ko, card_id)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(card_json, f, ensure_ascii=False, indent=2)

        print(f"  ✓ Created: {filename}")
        created_count += 1
        card_id += 1

print("\n" + "=" * 70)
print(f"✅ Successfully created {created_count} Minor Arcana card files!")
print(f"📁 Location: {base_path}")
