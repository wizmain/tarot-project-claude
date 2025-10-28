"""
Database Provider Interface

다양한 데이터베이스 백엔드(PostgreSQL, Firestore 등)를 추상화하는 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class Card:
    """타로 카드 데이터 모델"""
    def __init__(
        self,
        id: int,
        name_en: str,
        name_ko: str,
        arcana_type: str,
        number: Optional[int],
        suit: Optional[str],
        keywords_upright: List[str],
        keywords_reversed: List[str],
        description_ko: str,
        image_url: str,
    ):
        self.id = id
        self.name_en = name_en
        self.name_ko = name_ko
        self.arcana_type = arcana_type
        self.number = number
        self.suit = suit
        self.keywords_upright = keywords_upright
        self.keywords_reversed = keywords_reversed
        self.description_ko = description_ko
        self.image_url = image_url


class Reading:
    """타로 리딩 데이터 모델"""
    def __init__(
        self,
        id: str,
        user_id: str,
        question: str,
        spread_type: str,
        category: Optional[str],
        cards: List[Dict[str, Any]],
        interpretation: Dict[str, Any],
        created_at: datetime,
    ):
        self.id = id
        self.user_id = user_id
        self.question = question
        self.spread_type = spread_type
        self.category = category
        self.cards = cards
        self.interpretation = interpretation
        self.created_at = created_at


class DatabaseProvider(ABC):
    """
    Database Provider 추상 인터페이스

    모든 데이터베이스 구현체는 이 인터페이스를 구현해야 합니다.
    """

    # ==================== Card Operations ====================

    @abstractmethod
    async def get_card_by_id(self, card_id: int) -> Optional[Card]:
        """ID로 카드 조회"""
        pass

    @abstractmethod
    async def get_card_by_name(self, name: str) -> Optional[Card]:
        """이름으로 카드 조회"""
        pass

    @abstractmethod
    async def get_cards(
        self,
        skip: int = 0,
        limit: int = 100,
        arcana_type: Optional[str] = None,
        suit: Optional[str] = None,
    ) -> List[Card]:
        """카드 목록 조회 (필터링 및 페이지네이션)"""
        pass

    @abstractmethod
    async def get_total_cards_count(
        self,
        arcana_type: Optional[str] = None,
        suit: Optional[str] = None,
    ) -> int:
        """전체 카드 수 조회 (필터링 적용)"""
        pass

    @abstractmethod
    async def get_random_cards(self, count: int) -> List[Card]:
        """랜덤 카드 추출"""
        pass

    @abstractmethod
    async def create_card(self, card_data: Dict[str, Any]) -> Card:
        """카드 생성"""
        pass

    @abstractmethod
    async def update_card(self, card_id: int, card_data: Dict[str, Any]) -> Card:
        """카드 수정"""
        pass

    @abstractmethod
    async def delete_card(self, card_id: int) -> bool:
        """카드 삭제"""
        pass

    # ==================== Reading Operations ====================

    @abstractmethod
    async def create_reading(self, reading_data: Dict[str, Any]) -> Reading:
        """리딩 생성"""
        pass

    @abstractmethod
    async def get_reading_by_id(self, reading_id: str) -> Optional[Reading]:
        """ID로 리딩 조회"""
        pass

    @abstractmethod
    async def get_readings_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        spread_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Reading]:
        """사용자별 리딩 목록 조회"""
        pass

    @abstractmethod
    async def get_total_readings_count(
        self,
        user_id: str,
        spread_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """사용자별 전체 리딩 수 조회"""
        pass

    @abstractmethod
    async def update_reading(self, reading_id: str, reading_data: Dict[str, Any]) -> Reading:
        """리딩 수정"""
        pass

    @abstractmethod
    async def delete_reading(self, reading_id: str) -> bool:
        """리딩 삭제"""
        pass

    # ==================== Connection Management ====================

    @abstractmethod
    async def connect(self) -> None:
        """데이터베이스 연결"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """데이터베이스 연결 해제"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """데이터베이스 상태 확인"""
        pass
