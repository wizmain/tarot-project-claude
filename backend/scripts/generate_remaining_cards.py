"""
Generate knowledge base files for remaining tarot cards

This script generates JSON knowledge base files for all 78 tarot cards
that don't already have knowledge base entries.
"""
import json
import os
from pathlib import Path

# Card data structure with authentic tarot meanings
MAJOR_ARCANA = {
    7: {
        "name": "Strength",
        "name_ko": "힘",
        "deep_meaning": "Strength represents inner power, courage, and compassion. Unlike the Chariot's external force, this card speaks to the gentle mastery of one's instincts and emotions. The image of a woman calmly closing a lion's mouth symbolizes the triumph of the spirit over base nature. True strength lies not in domination but in patience, self-control, and loving-kindness. This card teaches that we overcome obstacles not through force but through understanding, and that real courage is about facing our fears with compassion rather than violence.",
        "symbolism": {
            "woman": "consciousness and compassion",
            "lion": "raw instincts and passions",
            "infinity_symbol": "infinite spiritual power",
            "white_robe": "purity of intention",
            "flowers": "beauty born from gentle care"
        },
        "upright_themes": ["inner strength", "courage", "compassion", "patience", "self-control", "gentle power"],
        "reversed_themes": ["self-doubt", "weakness", "insecurity", "lack of confidence", "abuse of power"],
        "astrological_association": "Leo",
        "element": "Fire",
        "life_lessons": "True power comes from within; gentleness can be stronger than force; patience and compassion overcome obstacles"
    },
    8: {
        "name": "The Hermit",
        "name_ko": "은둔자",
        "deep_meaning": "The Hermit represents introspection, solitude, and inner wisdom. Standing alone on a mountaintop with only a lantern to light the way, he symbolizes the journey inward to find truth. This is a time for withdrawal from the external world to focus on spiritual understanding and self-discovery. The Hermit teaches that sometimes we must step back from the noise of daily life to hear our inner voice. His light is both a beacon for others and illumination for his own path, suggesting that wisdom gained in solitude can eventually guide others.",
        "symbolism": {
            "lantern": "inner light and wisdom",
            "staff": "authority and support",
            "mountain": "spiritual achievement",
            "gray_cloak": "invisibility and neutrality",
            "six-pointed_star": "the seal of Solomon, divine wisdom"
        },
        "upright_themes": ["introspection", "solitude", "wisdom", "soul-searching", "inner guidance"],
        "reversed_themes": ["isolation", "loneliness", "withdrawal", "paranoia", "refusal to seek help"],
        "astrological_association": "Virgo",
        "element": "Earth"
    },
    9: {
        "name": "Wheel of Fortune",
        "name_ko": "운명의 수레바퀴",
        "deep_meaning": "The Wheel of Fortune represents cycles, destiny, and turning points. Life moves in cycles of good and bad fortune, and this card reminds us that change is the only constant. What goes up must come down, and what falls will rise again. The wheel teaches acceptance of life's natural rhythms and the understanding that we are part of something greater than ourselves. It speaks to karma, fate, and the interconnectedness of all things. When this card appears, significant change is afoot - embrace it rather than resist it.",
        "symbolism": {
            "wheel": "cycles and destiny",
            "sphinx": "riddles and mysteries",
            "snake": "descent and material nature",
            "anubis": "rise and divine nature",
            "four_creatures": "the four fixed signs and evangelists",
            "hebrew_letters": "YHVH, the name of God"
        },
        "upright_themes": ["change", "cycles", "destiny", "turning point", "good fortune"],
        "reversed_themes": ["bad luck", "resistance to change", "breaking cycles"],
        "astrological_association": "Jupiter",
        "element": "Fire"
    },
    10: {
        "name": "Justice",
        "name_ko": "정의",
        "deep_meaning": "Justice represents fairness, truth, and the law of cause and effect. She sits between two pillars holding scales and a sword, symbolizing balanced judgment and decisive action. This card reminds us that actions have consequences and that truth will ultimately prevail. Justice is about taking responsibility for our choices and understanding that we create our own reality through our decisions. It speaks to legal matters, contracts, and karmic balance. The card teaches that fairness requires both compassion and objectivity.",
        "symbolism": {
            "scales": "balance and fairness",
            "sword": "mental clarity and truth",
            "purple_cloak": "compassion and understanding",
            "crown": "clear thinking",
            "pillars": "law and structure"
        },
        "upright_themes": ["fairness", "truth", "law", "accountability", "karma"],
        "reversed_themes": ["unfairness", "dishonesty", "lack of accountability", "legal issues"],
        "astrological_association": "Libra",
        "element": "Air"
    },
    11: {
        "name": "The Hanged Man",
        "name_ko": "매달린 남자",
        "deep_meaning": "The Hanged Man represents surrender, new perspectives, and enlightenment through sacrifice. Hanging upside down from a tree, he appears calm and even serene, suggesting voluntary suspension and a different way of seeing the world. This card teaches that sometimes we must let go of control and allow events to unfold. The sacrifice here is not suffering but rather releasing old patterns to gain wisdom. By suspending action and accepting a period of waiting, we often gain insights that would never come through force or struggle.",
        "symbolism": {
            "upside_down_position": "new perspective",
            "halo": "spiritual enlightenment",
            "serene_expression": "peace in surrender",
            "one_leg_crossed": "the number 4, material stability",
            "living_tree": "growth continues even in suspension"
        },
        "upright_themes": ["surrender", "letting go", "new perspective", "enlightenment", "patience"],
        "reversed_themes": ["stalling", "resistance", "indecision", "missed opportunities"],
        "astrological_association": "Neptune",
        "element": "Water"
    },
    12: {
        "name": "Death",
        "name_ko": "죽음",
        "deep_meaning": "Death represents transformation, endings, and new beginnings. Despite its fearsome appearance, this card rarely signifies physical death. Instead, it speaks to profound change - the death of old ways, relationships, or beliefs to make room for new growth. Like autumn leaves falling to nourish spring flowers, Death teaches that endings are necessary for renewal. Resistance to this change causes suffering; acceptance brings liberation. This is one of the most misunderstood but ultimately hopeful cards in the deck.",
        "symbolism": {
            "skeleton": "what remains after transformation",
            "black_armor": "invincibility of death/change",
            "white_horse": "purity of the transformative force",
            "rising_sun": "rebirth and new beginnings",
            "fallen_king": "death comes to all regardless of status"
        },
        "upright_themes": ["transformation", "endings", "transition", "letting go", "new beginnings"],
        "reversed_themes": ["resistance to change", "stagnation", "fear of endings"],
        "astrological_association": "Scorpio",
        "element": "Water"
    },
    13: {
        "name": "Temperance",
        "name_ko": "절제",
        "deep_meaning": "Temperance represents balance, moderation, and harmony. An angel pours water between two cups, symbolizing the alchemical mixing of opposites to create something new. This card teaches the middle way - avoiding extremes and finding equilibrium in all things. Temperance is about patience, purpose, and the gradual blending of elements to achieve the perfect mix. It speaks to healing through balance and the importance of timing. True alchemy happens when we learn to moderate our energies and work with natural flows rather than against them.",
        "symbolism": {
            "angel": "higher guidance and protection",
            "two_cups": "balance of opposites",
            "water_flowing": "mixing of conscious and unconscious",
            "one_foot_on_land_one_in_water": "balance of material and spiritual",
            "iris_flowers": "the rainbow and hope"
        },
        "upright_themes": ["balance", "moderation", "patience", "purpose", "meaning"],
        "reversed_themes": ["imbalance", "excess", "lack of harmony", "impatience"],
        "astrological_association": "Sagittarius",
        "element": "Fire"
    },
    14: {
        "name": "The Devil",
        "name_ko": "악마",
        "deep_meaning": "The Devil represents bondage, materialism, and the shadow self. But look closely - the chains around the necks of the human figures are loose enough to remove. This card teaches that we are often prisoners of our own making, bound by unhealthy attachments, addictions, or limiting beliefs. The Devil is not an external force but our own shadow - the parts of ourselves we deny or repress. Freedom comes from acknowledging these aspects and recognizing that we have the power to release ourselves from self-imposed limitations.",
        "symbolism": {
            "inverted_pentagram": "material over spiritual",
            "loose_chains": "self-imposed bondage",
            "horns": "animal nature",
            "torch": "false light of materialism",
            "man_and_woman": "humanity in bondage"
        },
        "upright_themes": ["bondage", "addiction", "materialism", "playfulness", "sexuality"],
        "reversed_themes": ["releasing limitations", "detachment", "breaking free"],
        "astrological_association": "Capricorn",
        "element": "Earth"
    },
    15: {
        "name": "The Tower",
        "name_ko": "탑",
        "deep_meaning": "The Tower represents sudden upheaval, revelation, and the destruction of false structures. Lightning strikes a tower built on faulty foundations, sending people falling from its heights. This card speaks to those moments when everything we thought was solid comes crashing down. While frightening, The Tower is ultimately liberating - it destroys only what was built on lies, illusions, or shaky ground. The lightning is divine intervention, a wake-up call that, though painful, clears the way for rebuilding on truth and solid foundations.",
        "symbolism": {
            "lightning": "divine intervention and revelation",
            "falling_figures": "ego and false constructs falling away",
            "crown": "material thoughts being overthrown",
            "black_sky": "the unknown and chaos",
            "flames": "purification through destruction"
        },
        "upright_themes": ["sudden change", "upheaval", "revelation", "awakening", "liberation"],
        "reversed_themes": ["avoiding disaster", "fear of change", "delaying the inevitable"],
        "astrological_association": "Mars",
        "element": "Fire"
    },
    16: {
        "name": "The Star",
        "name_ko": "별",
        "deep_meaning": "The Star represents hope, renewal, and spiritual guidance. After the chaos of The Tower, The Star brings healing and serenity. A woman kneels by water, pouring it onto land and into the pool, symbolizing the flow of spiritual nourishment and the connection between conscious and unconscious. The stars above represent divine guidance and the promise that we are never truly lost. This card teaches that even in our darkest moments, hope remains. It speaks to faith, inspiration, and the calm certainty that everything will work out as it should.",
        "symbolism": {
            "naked_woman": "vulnerability and truth",
            "two_vessels": "conscious and unconscious mind",
            "pool": "the universal subconscious",
            "eight-pointed_star": "cosmic order and hope",
            "bird": "the sacred ibis, thought and spirituality"
        },
        "upright_themes": ["hope", "faith", "renewal", "inspiration", "serenity"],
        "reversed_themes": ["despair", "lack of faith", "disconnection"],
        "astrological_association": "Aquarius",
        "element": "Air"
    },
    17: {
        "name": "The Moon",
        "name_ko": "달",
        "deep_meaning": "The Moon represents illusion, intuition, and the unconscious mind. In the moonlight, nothing is quite as it seems - shadows deepen, and imagination runs wild. This card speaks to the realm of dreams, fears, and hidden truths. The path between two towers winds into the distance, uncertain and mysterious. The Moon teaches us to trust our intuition while remaining aware that our perceptions may be clouded by fear or projection. It asks us to explore our inner landscape and face what lurks in our unconscious.",
        "symbolism": {
            "moon": "the unconscious and intuition",
            "dog_and_wolf": "tamed and wild nature",
            "crayfish": "early stages of consciousness emerging",
            "path": "the journey into the unknown",
            "towers": "gates to the unconscious"
        },
        "upright_themes": ["illusion", "intuition", "uncertainty", "dreams", "subconscious"],
        "reversed_themes": ["confusion", "fear", "misinterpretation", "deception"],
        "astrological_association": "Pisces",
        "element": "Water"
    },
    18: {
        "name": "The Sun",
        "name_ko": "태양",
        "deep_meaning": "The Sun represents joy, success, and vitality. A child rides a white horse under a brilliant sun, embodying innocence, enthusiasm, and the pure joy of existence. After the confusion of The Moon, The Sun brings clarity, warmth, and certainty. Everything is illuminated; there are no shadows or hidden threats. This card teaches that life can be simple, joyful, and straightforward when we approach it with childlike wonder and authenticity. The Sun promises success, but more importantly, it speaks to the inner radiance that comes from being true to yourself.",
        "symbolism": {
            "sun": "consciousness and enlightenment",
            "child": "innocence and authenticity",
            "white_horse": "purity",
            "sunflowers": "life following the light",
            "nakedness": "nothing to hide, complete authenticity"
        },
        "upright_themes": ["joy", "success", "vitality", "confidence", "clarity"],
        "reversed_themes": ["dimmed joy", "temporary setbacks", "delayed success"],
        "astrological_association": "Sun",
        "element": "Fire"
    },
    19: {
        "name": "Judgement",
        "name_ko": "심판",
        "deep_meaning": "Judgement represents rebirth, inner calling, and absolution. An angel blows a trumpet, calling souls to rise from their graves - a moment of reckoning and renewal. This card speaks to those times when we are called to a higher purpose or asked to evaluate our lives and choices. Judgement is about self-reflection, forgiveness, and the opportunity to leave the past behind. It's a spiritual awakening, a moment of clarity where we see ourselves and our path with perfect honesty. The card teaches that we are constantly given chances to begin anew.",
        "symbolism": {
            "angel": "divine calling",
            "trumpet": "wake-up call",
            "people_rising": "resurrection and renewal",
            "mountains": "immovable truth",
            "cross_on_flag": "balance of polarities"
        },
        "upright_themes": ["rebirth", "inner calling", "absolution", "evaluation"],
        "reversed_themes": ["self-doubt", "self-criticism", "inability to move forward"],
        "astrological_association": "Pluto",
        "element": "Fire"
    },
    20: {
        "name": "The World",
        "name_ko": "세계",
        "deep_meaning": "The World represents completion, achievement, and cosmic consciousness. A dancer moves within a cosmic wreath, surrounded by the four elements, symbolizing perfect harmony and the successful conclusion of a journey. This is the final card of the Major Arcana - the Fool has traveled the entire journey and arrived at enlightenment. The World teaches that every ending is also a new beginning, and that completion of one cycle prepares us for the next. It speaks to fulfillment, integration, and the joy of knowing you have accomplished what you set out to do.",
        "symbolism": {
            "dancing_figure": "cosmic consciousness and celebration",
            "wreath": "completion and victory",
            "four_creatures": "four elements in balance",
            "two_wands": "balance and achievement",
            "purple_cloth": "wisdom and luxury"
        },
        "upright_themes": ["completion", "accomplishment", "travel", "cosmic awareness"],
        "reversed_themes": ["incompletion", "lack of closure", "short-cuts"],
        "astrological_association": "Saturn",
        "element": "Earth"
    }
}

# Generate a script that creates all remaining card files
print("Generating remaining tarot card knowledge base files...")
print("=" * 70)

# This script will need to be expanded with all minor arcana cards
# For now, let's create a template that can be used

template = {
    "id": 0,
    "name": "",
    "name_ko": "",
    "arcana_type": "major",
    "rank": "",
    "number": 0,
    "deep_meaning": "",
    "deep_meaning_ko": "",
    "symbolism": {},
    "upright_themes": [],
    "reversed_themes": [],
    "upright_extended": "",
    "reversed_extended": "",
    "life_lessons": "",
    "related_cards": [],
    "astrological_association": "",
    "element": "",
    "numerology": "",
    "questions_to_ask": []
}

# Create directories
base_path = Path("/Users/wizmain/Documents/workspace/tarot-project-claude/backend/data/knowledge_base/cards")
major_path = base_path / "major_arcana"
minor_path = base_path / "minor_arcana"

# Ensure directories exist
major_path.mkdir(parents=True, exist_ok=True)
for suit in ["wands", "cups", "swords", "pentacles"]:
    (minor_path / suit).mkdir(parents=True, exist_ok=True)

# Create Major Arcana files (7-20)
created_count = 0
for card_id, card_data in MAJOR_ARCANA.items():
    filename = f"{card_id:02d}_{card_data['name'].lower().replace(' ', '_')}.json"
    filepath = major_path / filename

    if not filepath.exists():
        card_json = {
            "id": card_id,
            "name": card_data["name"],
            "name_ko": card_data["name_ko"],
            "arcana_type": "major",
            "rank": card_data["name"],
            "number": card_id,
            "deep_meaning": card_data["deep_meaning"],
            "deep_meaning_ko": f"{card_data['name_ko']}는 {card_data['upright_themes'][0]}을/를 상징합니다.",
            "symbolism": card_data["symbolism"],
            "upright_themes": card_data["upright_themes"],
            "reversed_themes": card_data["reversed_themes"],
            "upright_extended": card_data["deep_meaning"],
            "reversed_extended": f"역방향에서 {card_data['name']}는 {', '.join(card_data['reversed_themes'][:3])}을 나타냅니다.",
            "life_lessons": card_data.get("life_lessons", ""),
            "related_cards": [],
            "astrological_association": card_data.get("astrological_association", ""),
            "element": card_data.get("element", ""),
            "numerology": f"Number {card_id} represents completion and spiritual attainment.",
            "questions_to_ask": [
                f"How can I embody the energy of {card_data['name']}?",
                f"What does {card_data['name']} teach me about my current situation?"
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(card_json, f, ensure_ascii=False, indent=2)

        created_count += 1
        print(f"✓ Created: {filename}")

print(f"\n✅ Successfully created {created_count} Major Arcana card files!")
print(f"📁 Location: {major_path}")
print("\n" + "=" * 70)
print("Note: Minor Arcana cards need to be generated separately")
print("      due to their large number (56 cards total)")
