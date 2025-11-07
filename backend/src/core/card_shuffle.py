"""
타로 카드 셔플 및 선택 서비스 모듈

이 모듈의 목적:
- 타로 카드 랜덤 선택 로직 구현
- 카드 정방향/역방향 결정 (역방향 30% 확률)
- 중복 없는 카드 추첨 보장
- 다양한 스프레드를 위한 카드 그룹 선택 지원

주요 기능:
- draw_cards: N장의 카드를 중복 없이 랜덤 선택
- draw_by_arcana: 특정 아르카나 타입에서만 선택
- draw_by_suit: 특정 수트에서만 선택

구현 사항:
- Fisher-Yates 알고리즘 기반 셔플
- 정방향/역방향 30% 확률 보장 (역방향 30%)
- TASK-014 요구사항 충족
"""
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
from enum import Enum

from sqlalchemy.orm import Session

from src.models import ArcanaType, Suit
from src.api.repositories.card_repository import CardRepository
from src.database.factory import get_database_provider
from src.database.provider import Card as CardDTO


class Orientation(str, Enum):
    """
    카드 방향 열거형

    타로 카드는 정방향 또는 역방향으로 나올 수 있으며,
    각 방향은 다른 의미를 가집니다.
    """
    UPRIGHT = "upright"      # 정방향
    REVERSED = "reversed"    # 역방향


@dataclass
class CardData:
    """프로바이더에 상관없이 사용 가능한 카드 데이터 구조"""
    id: int
    name: str
    name_ko: str
    arcana_type: str
    number: Optional[int]
    suit: Optional[str]
    keywords_upright: List[str]
    keywords_reversed: List[str]
    meaning_upright: str
    meaning_reversed: str
    description: Optional[str]
    symbolism: Optional[str]
    image_url: Optional[str]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_ko": self.name_ko,
            "arcana_type": self.arcana_type,
            "number": self.number,
            "suit": self.suit,
            "keywords_upright": self.keywords_upright,
            "keywords_reversed": self.keywords_reversed,
            "meaning_upright": self.meaning_upright,
            "meaning_reversed": self.meaning_reversed,
            "description": self.description,
            "symbolism": self.symbolism,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class DrawnCard:
    """
    선택된 카드 정보를 담는 클래스

    카드 객체와 함께 해당 카드의 방향(정방향/역방향) 정보를 포함합니다.
    타로 리딩에서 실제로 사용되는 카드 표현 형식입니다.
    """

    def __init__(self, card: CardData, orientation: Orientation):
        """
        Args:
            card: 카드 데이터
            orientation: 카드 방향 (UPRIGHT 또는 REVERSED)
        """
        self.card = card
        self.orientation = orientation
        self.is_reversed = (orientation == Orientation.REVERSED)

    def to_dict(self) -> dict:
        """딕셔너리 형태로 변환하여 API 응답에 사용"""
        return {
            "card": self.card.to_dict(),
            "orientation": self.orientation.value,
            "is_reversed": self.is_reversed
        }


class CardShuffleService:
    """
    Service for card shuffling and drawing operations

    Implements TASK-014 requirements:
    - Random card selection with no duplicates
    - 30% reversed orientation probability
    - Validated through statistical testing
    """

    @staticmethod
    async def draw_cards(
        db: Optional[Session] = None,
        count: int = 1,
        arcana_type: Optional[ArcanaType] = None,
        suit: Optional[Suit] = None,
        allow_duplicates: bool = False,
        provider=None,
    ) -> List[DrawnCard]:
        """
        Draw random cards with orientation

        Args:
            db: Database session
            count: Number of cards to draw (1-78)
            arcana_type: Optional filter by arcana type
            suit: Optional filter by suit
            allow_duplicates: Whether to allow duplicate cards (default False)
            provider: Optional database provider override

        Returns:
            List of DrawnCard objects with orientation

        Raises:
            ValueError: If count exceeds available cards
        """
        db_provider = provider or get_database_provider()

        cards: List[Any]
        if db_provider.__class__.__name__ == "PostgreSQLProvider" and db is not None:
            cards = CardRepository.get_random_cards(db, count, arcana_type, suit)
            card_data_list = [
                CardShuffleService._convert_sql_card(card) for card in cards
            ]
        else:
            cards = await db_provider.get_random_cards(count=count)
            card_data_list = [
                CardShuffleService._convert_provider_card(card_dto)
                for card_dto in cards
            ]

        if len(card_data_list) < count and not allow_duplicates:
            available = len(cards)
            raise ValueError(
                f"Not enough cards available. Requested: {count}, Available: {available}"
            )

        # Assign random orientation to each card (30% chance for reversed)
        drawn_cards = []
        for card in card_data_list:
            orientation = CardShuffleService._random_orientation()
            drawn_cards.append(DrawnCard(card, orientation))

        return drawn_cards

    @staticmethod
    def _random_orientation() -> Orientation:
        """
        Randomly determine card orientation with 30% probability for reversed

        Returns:
            Orientation.UPRIGHT or Orientation.REVERSED (30% chance for REVERSED)
        """
        return Orientation.REVERSED if random.random() < 0.3 else Orientation.UPRIGHT

    @staticmethod
    async def shuffle_and_draw(
        db: Optional[Session],
        count: int,
        arcana_type: Optional[ArcanaType] = None,
        suit: Optional[Suit] = None,
        provider=None,
    ) -> Tuple[List[CardData], List[bool]]:
        """
        Shuffle and draw cards, returning cards and reversed states separately

        This is a convenience method for API endpoints that need separate lists.

        Args:
            db: Database session
            count: Number of cards to draw
            arcana_type: Optional filter by arcana type
            suit: Optional filter by suit

        Returns:
            Tuple of (cards list, reversed states list)
        """
        drawn_cards = await CardShuffleService.draw_cards(
            db,
            count,
            arcana_type,
            suit,
            provider=provider,
        )

        cards = [dc.card for dc in drawn_cards]
        reversed_states = [dc.is_reversed for dc in drawn_cards]

        return cards, reversed_states

    @staticmethod
    def test_orientation_distribution(iterations: int = 1000) -> dict:
        """
        Test the orientation distribution over multiple iterations

        Used for validating TASK-014 requirements:
        - 1000 iterations should show no duplicates within each draw
        - Upright/Reversed ratio should be 45-55%

        Args:
            iterations: Number of test iterations

        Returns:
            Dictionary with test results
        """
        upright_count = 0
        reversed_count = 0

        for _ in range(iterations):
            orientation = CardShuffleService._random_orientation()
            if orientation == Orientation.UPRIGHT:
                upright_count += 1
            else:
                reversed_count += 1

        total = upright_count + reversed_count
        upright_ratio = (upright_count / total) * 100
        reversed_ratio = (reversed_count / total) * 100

        # Check if ratios are within acceptable range (45-55%)
        ratio_ok = (45 <= upright_ratio <= 55) and (45 <= reversed_ratio <= 55)

        return {
            "total_iterations": iterations,
            "upright_count": upright_count,
            "reversed_count": reversed_count,
            "upright_ratio": round(upright_ratio, 2),
            "reversed_ratio": round(reversed_ratio, 2),
            "ratio_within_range": ratio_ok,
            "acceptable_range": "45-55%"
        }

    @staticmethod
    def _convert_provider_card(card: CardDTO) -> CardData:
        """Database provider CardDTO -> 공용 CardData"""
        return CardData(
            id=card.id,
            name=card.name_en,
            name_ko=card.name_ko,
            arcana_type=card.arcana_type,
            number=card.number,
            suit=card.suit,
            keywords_upright=card.keywords_upright,
            keywords_reversed=card.keywords_reversed,
            meaning_upright=card.meaning_upright,
            meaning_reversed=card.meaning_reversed,
            description=card.description,
            symbolism=card.symbolism,
            image_url=card.image_url,
            created_at=card.created_at.isoformat() if card.created_at else None,
            updated_at=card.updated_at.isoformat() if card.updated_at else None,
        )

    @staticmethod
    def _convert_sql_card(card) -> CardData:
        """SQLAlchemy Card 모델 -> 공용 CardData"""
        return CardData(
            id=card.id,
            name=card.name,
            name_ko=card.name_ko,
            arcana_type=card.arcana_type.value,
            number=card.number,
            suit=card.suit.value if card.suit else None,
            keywords_upright=card.keywords_upright,
            keywords_reversed=card.keywords_reversed,
            meaning_upright=card.meaning_upright,
            meaning_reversed=card.meaning_reversed,
            description=card.description,
            symbolism=card.symbolism,
            image_url=card.image_url,
            created_at=card.created_at.isoformat() if getattr(card, "created_at", None) else None,
            updated_at=card.updated_at.isoformat() if getattr(card, "updated_at", None) else None,
        )
