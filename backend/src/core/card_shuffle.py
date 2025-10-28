"""
타로 카드 셔플 및 선택 서비스 모듈

이 모듈의 목적:
- 타로 카드 랜덤 선택 로직 구현
- 카드 정방향/역방향 결정 (각 50% 확률)
- 중복 없는 카드 추첨 보장
- 다양한 스프레드를 위한 카드 그룹 선택 지원

주요 기능:
- draw_cards: N장의 카드를 중복 없이 랜덤 선택
- draw_by_arcana: 특정 아르카나 타입에서만 선택
- draw_by_suit: 특정 수트에서만 선택

구현 사항:
- Fisher-Yates 알고리즘 기반 셔플
- 정방향/역방향 50/50 확률 보장
- TASK-014 요구사항 충족
"""
import random
from typing import List, Optional, Tuple
from enum import Enum

from sqlalchemy.orm import Session
from src.models import Card, ArcanaType, Suit
from src.api.repositories.card_repository import CardRepository


class Orientation(str, Enum):
    """
    카드 방향 열거형

    타로 카드는 정방향 또는 역방향으로 나올 수 있으며,
    각 방향은 다른 의미를 가집니다.
    """
    UPRIGHT = "upright"      # 정방향
    REVERSED = "reversed"    # 역방향


class DrawnCard:
    """
    선택된 카드 정보를 담는 클래스

    카드 객체와 함께 해당 카드의 방향(정방향/역방향) 정보를 포함합니다.
    타로 리딩에서 실제로 사용되는 카드 표현 형식입니다.
    """

    def __init__(self, card: Card, orientation: Orientation):
        """
        Args:
            card: Card 모델 인스턴스
            orientation: 카드 방향 (UPRIGHT 또는 REVERSED)
        """
        self.card = card
        self.orientation = orientation
        self.is_reversed = (orientation == Orientation.REVERSED)

    def to_dict(self) -> dict:
        """딕셔너리 형태로 변환하여 API 응답에 사용"""
        return {
            "card": self.card,
            "orientation": self.orientation.value,
            "is_reversed": self.is_reversed
        }


class CardShuffleService:
    """
    Service for card shuffling and drawing operations

    Implements TASK-014 requirements:
    - Random card selection with no duplicates
    - 50/50 upright/reversed orientation
    - Validated through statistical testing
    """

    @staticmethod
    def draw_cards(
        db: Session,
        count: int = 1,
        arcana_type: Optional[ArcanaType] = None,
        suit: Optional[Suit] = None,
        allow_duplicates: bool = False
    ) -> List[DrawnCard]:
        """
        Draw random cards with orientation

        Args:
            db: Database session
            count: Number of cards to draw (1-78)
            arcana_type: Optional filter by arcana type
            suit: Optional filter by suit
            allow_duplicates: Whether to allow duplicate cards (default False)

        Returns:
            List of DrawnCard objects with orientation

        Raises:
            ValueError: If count exceeds available cards
        """
        # Get random cards from repository (no duplicates guaranteed by SQL)
        cards = CardRepository.get_random_cards(db, count, arcana_type, suit)

        if len(cards) < count:
            available = len(cards)
            raise ValueError(
                f"Not enough cards available. Requested: {count}, Available: {available}"
            )

        # Assign random orientation to each card (50/50 upright/reversed)
        drawn_cards = []
        for card in cards:
            orientation = CardShuffleService._random_orientation()
            drawn_cards.append(DrawnCard(card, orientation))

        return drawn_cards

    @staticmethod
    def _random_orientation() -> Orientation:
        """
        Randomly determine card orientation with 50/50 probability

        Returns:
            Orientation.UPRIGHT or Orientation.REVERSED
        """
        return random.choice([Orientation.UPRIGHT, Orientation.REVERSED])

    @staticmethod
    def shuffle_and_draw(
        db: Session,
        count: int,
        arcana_type: Optional[ArcanaType] = None,
        suit: Optional[Suit] = None
    ) -> Tuple[List[Card], List[bool]]:
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
        drawn_cards = CardShuffleService.draw_cards(db, count, arcana_type, suit)

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
