"""
Unit tests for Card Shuffle Service (TASK-014)

Tests verify:
- No duplicate cards in draws
- 50/50 upright/reversed orientation distribution
- Proper handling of filters and edge cases
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.card_shuffle import CardShuffleService, Orientation, DrawnCard
from src.models import Card, ArcanaType, Suit
from src.core.database import Base


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Create test cards
    test_cards = [
        Card(
            name=f"Test Card {i}",
            name_ko=f"테스트 카드 {i}",
            number=i if i < 22 else None,
            arcana_type=ArcanaType.MAJOR if i < 22 else ArcanaType.MINOR,
            suit=Suit.WANDS if i >= 22 else None,
            keywords_upright=["test", "keyword"],
            keywords_reversed=["reversed", "test"],
            meaning_upright="Test meaning upright",
            meaning_reversed="Test meaning reversed",
            description="Test description",
            symbolism="Test symbolism"
        )
        for i in range(78)
    ]

    session.add_all(test_cards)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


class TestCardShuffleService:
    """Test suite for CardShuffleService"""

    def test_draw_single_card(self, db_session):
        """Test drawing a single card"""
        drawn_cards = CardShuffleService.draw_cards(db_session, count=1)

        assert len(drawn_cards) == 1
        assert isinstance(drawn_cards[0], DrawnCard)
        assert isinstance(drawn_cards[0].card, Card)
        assert drawn_cards[0].orientation in [Orientation.UPRIGHT, Orientation.REVERSED]

    def test_draw_multiple_cards(self, db_session):
        """Test drawing multiple cards"""
        count = 5
        drawn_cards = CardShuffleService.draw_cards(db_session, count=count)

        assert len(drawn_cards) == count

        # Verify all are DrawnCard instances
        for dc in drawn_cards:
            assert isinstance(dc, DrawnCard)
            assert isinstance(dc.card, Card)

    def test_no_duplicate_cards(self, db_session):
        """Test that no duplicate cards are drawn (TASK-014 requirement)"""
        count = 10
        drawn_cards = CardShuffleService.draw_cards(db_session, count=count)

        # Get card IDs
        card_ids = [dc.card.id for dc in drawn_cards]

        # Check for duplicates
        assert len(card_ids) == len(set(card_ids)), "Duplicate cards were drawn!"

    def test_no_duplicates_1000_iterations(self, db_session):
        """
        Test no duplicates over 1000 iterations (TASK-014 requirement)
        Each iteration draws 10 cards and checks for duplicates
        """
        failures = 0

        for _ in range(1000):
            drawn_cards = CardShuffleService.draw_cards(db_session, count=10)
            card_ids = [dc.card.id for dc in drawn_cards]

            if len(card_ids) != len(set(card_ids)):
                failures += 1

        # TASK-014 requirement: 0% duplicate rate
        assert failures == 0, f"Found duplicates in {failures}/1000 iterations"

    def test_orientation_distribution(self):
        """
        Test orientation distribution over 1000 iterations (TASK-014 requirement)
        Should be within 45-55% range
        """
        result = CardShuffleService.test_orientation_distribution(iterations=1000)

        assert result["total_iterations"] == 1000
        assert result["upright_count"] + result["reversed_count"] == 1000

        # TASK-014 requirement: 45-55% range
        assert result["ratio_within_range"], \
            f"Orientation ratio out of range: Upright {result['upright_ratio']}%, " \
            f"Reversed {result['reversed_ratio']}%"

    def test_orientation_distribution_10000_iterations(self):
        """Test orientation distribution with larger sample size"""
        result = CardShuffleService.test_orientation_distribution(iterations=10000)

        # With 10000 iterations, should be very close to 50/50
        upright_ratio = result["upright_ratio"]
        reversed_ratio = result["reversed_ratio"]

        # Should be within 45-55% range (more lenient for statistical variation)
        assert 45 <= upright_ratio <= 55, f"Upright ratio {upright_ratio}% out of range"
        assert 45 <= reversed_ratio <= 55, f"Reversed ratio {reversed_ratio}% out of range"

    def test_draw_with_arcana_filter(self, db_session):
        """Test drawing cards with arcana type filter"""
        # Draw only major arcana
        drawn_cards = CardShuffleService.draw_cards(
            db_session,
            count=5,
            arcana_type=ArcanaType.MAJOR
        )

        assert len(drawn_cards) == 5

        # Verify all are major arcana
        for dc in drawn_cards:
            assert dc.card.arcana_type == ArcanaType.MAJOR

    def test_draw_exceeds_available(self, db_session):
        """Test error when requesting more cards than available"""
        with pytest.raises(ValueError, match="Not enough cards available"):
            # Try to draw more cards than exist
            CardShuffleService.draw_cards(db_session, count=100)

    def test_shuffle_and_draw_returns_separate_lists(self, db_session):
        """Test shuffle_and_draw convenience method"""
        cards, reversed_states = CardShuffleService.shuffle_and_draw(
            db_session,
            count=5
        )

        assert len(cards) == 5
        assert len(reversed_states) == 5

        # Verify types
        for card in cards:
            assert isinstance(card, Card)

        for state in reversed_states:
            assert isinstance(state, bool)

    def test_drawn_card_to_dict(self, db_session):
        """Test DrawnCard.to_dict() method"""
        drawn_cards = CardShuffleService.draw_cards(db_session, count=1)
        dc = drawn_cards[0]

        result = dc.to_dict()

        assert "card" in result
        assert "orientation" in result
        assert "is_reversed" in result
        assert result["orientation"] in ["upright", "reversed"]
        assert isinstance(result["is_reversed"], bool)

    def test_random_orientation_method(self):
        """Test the _random_orientation method"""
        orientations = [
            CardShuffleService._random_orientation()
            for _ in range(100)
        ]

        # Should have both orientations present
        assert Orientation.UPRIGHT in orientations
        assert Orientation.REVERSED in orientations

        # All should be valid orientations
        for orientation in orientations:
            assert orientation in [Orientation.UPRIGHT, Orientation.REVERSED]


class TestDrawnCard:
    """Test suite for DrawnCard class"""

    def test_upright_card(self, db_session):
        """Test DrawnCard with upright orientation"""
        card = db_session.query(Card).first()
        dc = DrawnCard(card, Orientation.UPRIGHT)

        assert dc.card == card
        assert dc.orientation == Orientation.UPRIGHT
        assert dc.is_reversed is False

    def test_reversed_card(self, db_session):
        """Test DrawnCard with reversed orientation"""
        card = db_session.query(Card).first()
        dc = DrawnCard(card, Orientation.REVERSED)

        assert dc.card == card
        assert dc.orientation == Orientation.REVERSED
        assert dc.is_reversed is True
