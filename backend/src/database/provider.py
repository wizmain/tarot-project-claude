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
        meaning_upright: str,
        meaning_reversed: str,
        description: Optional[str],
        symbolism: Optional[str],
        image_url: Optional[str],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name_en = name_en
        self.name_ko = name_ko
        self.arcana_type = arcana_type
        self.number = number
        self.suit = suit
        self.keywords_upright = keywords_upright
        self.keywords_reversed = keywords_reversed
        self.meaning_upright = meaning_upright
        self.meaning_reversed = meaning_reversed
        self.description = description
        self.symbolism = symbolism
        self.image_url = image_url
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """카드 데이터를 API 응답 형식으로 변환"""
        return {
            "id": self.id,
            "name": self.name_en,
            "name_ko": self.name_ko,
            "number": self.number,
            "arcana_type": self.arcana_type,
            "suit": self.suit,
            "keywords_upright": self.keywords_upright,
            "keywords_reversed": self.keywords_reversed,
            "meaning_upright": self.meaning_upright,
            "meaning_reversed": self.meaning_reversed,
            "description": self.description,
            "symbolism": self.symbolism,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LLMUsageLog:
    """LLM 사용 기록 데이터 모델"""
    def __init__(
        self,
        id: str,
        reading_id: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost: float,
        latency_seconds: float,
        purpose: str = "main_reading",
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.reading_id = reading_id
        self.provider = provider
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.estimated_cost = estimated_cost
        self.latency_seconds = latency_seconds
        self.purpose = purpose
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """LLM 사용 로그를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "reading_id": self.reading_id,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost,
            "latency_seconds": self.latency_seconds,
            "purpose": self.purpose,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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
        card_relationships: Optional[str],
        overall_reading: str,
        advice: Dict[str, Any],
        summary: str,
        created_at: datetime,
        updated_at: Optional[datetime] = None,
        llm_usage: Optional[List[Dict[str, Any]]] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.question = question
        self.spread_type = spread_type
        self.category = category
        self.cards = cards
        self.card_relationships = card_relationships
        self.overall_reading = overall_reading
        self.advice = advice
        self.summary = summary
        self.created_at = created_at
        self.updated_at = updated_at
        self.llm_usage = llm_usage or []

    def to_dict(self) -> Dict[str, Any]:
        """리딩 데이터를 API 응답 형식으로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question": self.question,
            "spread_type": self.spread_type,
            "category": self.category,
            "cards": self.cards,
            "card_relationships": self.card_relationships,
            "overall_reading": self.overall_reading,
            "advice": self.advice,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "llm_usage": self.llm_usage,
        }


class Feedback:
    """피드백 데이터 모델"""
    def __init__(
        self,
        id: str,
        reading_id: str,
        user_id: str,
        rating: int,
        comment: Optional[str],
        helpful: bool,
        accurate: bool,
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.reading_id = reading_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.helpful = helpful
        self.accurate = accurate
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "reading_id": self.reading_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
            "helpful": self.helpful,
            "accurate": self.accurate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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

    # ==================== LLM Usage Log Operations ====================

    @abstractmethod
    async def create_llm_usage_log(self, log_data: Dict[str, Any]) -> LLMUsageLog:
        """LLM 사용 로그 생성"""
        pass

    @abstractmethod
    async def get_llm_usage_logs(self, reading_id: str) -> List[LLMUsageLog]:
        """특정 리딩의 LLM 사용 로그 조회"""
        pass

    # ==================== Feedback Operations ====================

    @abstractmethod
    async def create_feedback(self, feedback_data: Dict[str, Any]) -> Feedback:
        """피드백 생성"""
        pass

    @abstractmethod
    async def get_feedback_by_id(self, feedback_id: str) -> Optional[Feedback]:
        """ID로 피드백 조회"""
        pass

    @abstractmethod
    async def get_feedback_by_reading(
        self,
        reading_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Feedback]:
        """특정 리딩의 피드백 목록 조회"""
        pass

    @abstractmethod
    async def get_feedback_by_reading_and_user(
        self,
        reading_id: str,
        user_id: str,
    ) -> Optional[Feedback]:
        """리딩과 사용자 조합으로 피드백 조회"""
        pass

    @abstractmethod
    async def update_feedback(
        self,
        feedback_id: str,
        feedback_data: Dict[str, Any],
    ) -> Optional[Feedback]:
        """피드백 수정"""
        pass

    @abstractmethod
    async def delete_feedback(self, feedback_id: str) -> bool:
        """피드백 삭제"""
        pass

    @abstractmethod
    async def get_feedback_statistics(self) -> Dict[str, Any]:
        """전체 피드백 통계"""
        pass

    @abstractmethod
    async def get_feedback_statistics_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """기간별 피드백 통계"""
        pass

    @abstractmethod
    async def get_feedback_statistics_by_spread_type(self) -> List[Dict[str, Any]]:
        """스프레드 타입별 피드백 통계"""
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
