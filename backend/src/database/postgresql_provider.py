"""
PostgreSQL Database Provider

기존 SQLAlchemy 모델을 사용하는 DatabaseProvider 구현체
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import random

from .provider import DatabaseProvider, Card as CardDTO, Reading as ReadingDTO
from src.core.database import SessionLocal
from src.models.card import Card as CardModel, ArcanaType, Suit
from src.models.reading import Reading as ReadingModel, ReadingCard


class PostgreSQLProvider(DatabaseProvider):
    """
    PostgreSQL 데이터베이스 Provider

    기존 SQLAlchemy 모델을 DatabaseProvider 인터페이스로 래핑합니다.
    """

    def __init__(self):
        """Initialize PostgreSQL provider"""
        self._session: Optional[Session] = None

    def _get_session(self) -> Session:
        """Get or create database session"""
        if self._session is None:
            self._session = SessionLocal()
        return self._session

    # ==================== Conversion Methods ====================

    def _model_to_card_dto(self, card_model: CardModel) -> CardDTO:
        """Convert SQLAlchemy Card model to Card DTO"""
        return CardDTO(
            id=card_model.id,
            name_en=card_model.name,
            name_ko=card_model.name_ko,
            arcana_type=card_model.arcana_type.value,
            number=card_model.number,
            suit=card_model.suit.value if card_model.suit else None,
            keywords_upright=card_model.keywords_upright,
            keywords_reversed=card_model.keywords_reversed,
            description_ko=card_model.description or "",
            image_url=card_model.image_url or "",
        )

    def _model_to_reading_dto(self, reading_model: ReadingModel) -> ReadingDTO:
        """Convert SQLAlchemy Reading model to Reading DTO"""
        cards = []
        for reading_card in reading_model.cards:
            card_data = {
                "card_id": reading_card.card_id,
                "position": reading_card.position,
                "orientation": reading_card.orientation,
                "interpretation": reading_card.interpretation,
                "key_message": reading_card.key_message,
                "card": {
                    "id": reading_card.card.id,
                    "name_en": reading_card.card.name,
                    "name_ko": reading_card.card.name_ko,
                    "arcana_type": reading_card.card.arcana_type.value,
                    "suit": reading_card.card.suit.value if reading_card.card.suit else None,
                    "image_url": reading_card.card.image_url,
                }
            }
            cards.append(card_data)

        interpretation = {
            "card_relationships": reading_model.card_relationships,
            "overall_reading": reading_model.overall_reading,
            "advice": reading_model.advice,
            "summary": reading_model.summary,
        }

        return ReadingDTO(
            id=str(reading_model.id),
            user_id=str(reading_model.user_id) if reading_model.user_id else "anonymous",
            question=reading_model.question,
            spread_type=reading_model.spread_type,
            category=reading_model.category,
            cards=cards,
            interpretation=interpretation,
            created_at=reading_model.created_at,
        )

    # ==================== Card Operations ====================

    async def get_card_by_id(self, card_id: int) -> Optional[CardDTO]:
        """ID로 카드 조회"""
        db = self._get_session()
        card_model = db.query(CardModel).filter(CardModel.id == card_id).first()
        if not card_model:
            return None
        return self._model_to_card_dto(card_model)

    async def get_card_by_name(self, name: str) -> Optional[CardDTO]:
        """이름으로 카드 조회"""
        db = self._get_session()
        card_model = db.query(CardModel).filter(
            or_(CardModel.name == name, CardModel.name_ko == name)
        ).first()
        if not card_model:
            return None
        return self._model_to_card_dto(card_model)

    async def get_cards(
        self,
        skip: int = 0,
        limit: int = 100,
        arcana_type: Optional[str] = None,
        suit: Optional[str] = None,
    ) -> List[CardDTO]:
        """카드 목록 조회 (필터링 및 페이지네이션)"""
        db = self._get_session()
        query = db.query(CardModel)

        # Apply filters
        if arcana_type:
            query = query.filter(CardModel.arcana_type == ArcanaType(arcana_type))
        if suit:
            query = query.filter(CardModel.suit == Suit(suit))

        # Apply pagination
        card_models = query.offset(skip).limit(limit).all()
        return [self._model_to_card_dto(card) for card in card_models]

    async def get_total_cards_count(
        self,
        arcana_type: Optional[str] = None,
        suit: Optional[str] = None,
    ) -> int:
        """전체 카드 수 조회 (필터링 적용)"""
        db = self._get_session()
        query = db.query(func.count(CardModel.id))

        # Apply filters
        if arcana_type:
            query = query.filter(CardModel.arcana_type == ArcanaType(arcana_type))
        if suit:
            query = query.filter(CardModel.suit == Suit(suit))

        return query.scalar()

    async def get_random_cards(self, count: int) -> List[CardDTO]:
        """랜덤 카드 추출"""
        db = self._get_session()
        total_cards = db.query(func.count(CardModel.id)).scalar()

        # Get random IDs
        random_ids = random.sample(range(1, total_cards + 1), min(count, total_cards))

        # Fetch cards
        card_models = db.query(CardModel).filter(CardModel.id.in_(random_ids)).all()
        return [self._model_to_card_dto(card) for card in card_models]

    async def create_card(self, card_data: Dict[str, Any]) -> CardDTO:
        """카드 생성"""
        db = self._get_session()

        card_model = CardModel(
            name=card_data["name_en"],
            name_ko=card_data["name_ko"],
            number=card_data.get("number"),
            arcana_type=ArcanaType(card_data["arcana_type"]),
            suit=Suit(card_data["suit"]) if card_data.get("suit") else None,
            keywords_upright=card_data["keywords_upright"],
            keywords_reversed=card_data["keywords_reversed"],
            meaning_upright=card_data.get("meaning_upright", ""),
            meaning_reversed=card_data.get("meaning_reversed", ""),
            description=card_data.get("description_ko", ""),
            symbolism=card_data.get("symbolism"),
            image_url=card_data.get("image_url", ""),
        )

        db.add(card_model)
        db.commit()
        db.refresh(card_model)

        return self._model_to_card_dto(card_model)

    async def update_card(self, card_id: int, card_data: Dict[str, Any]) -> CardDTO:
        """카드 수정"""
        db = self._get_session()
        card_model = db.query(CardModel).filter(CardModel.id == card_id).first()

        if not card_model:
            raise ValueError(f"Card with id {card_id} not found")

        # Update fields
        for key, value in card_data.items():
            if hasattr(card_model, key):
                setattr(card_model, key, value)

        db.commit()
        db.refresh(card_model)

        return self._model_to_card_dto(card_model)

    async def delete_card(self, card_id: int) -> bool:
        """카드 삭제"""
        db = self._get_session()
        card_model = db.query(CardModel).filter(CardModel.id == card_id).first()

        if not card_model:
            return False

        db.delete(card_model)
        db.commit()
        return True

    # ==================== Reading Operations ====================

    async def create_reading(self, reading_data: Dict[str, Any]) -> ReadingDTO:
        """리딩 생성"""
        db = self._get_session()

        # Create Reading
        reading_model = ReadingModel(
            user_id=reading_data.get("user_id"),
            spread_type=reading_data["spread_type"],
            question=reading_data["question"],
            category=reading_data.get("category"),
            card_relationships=reading_data.get("card_relationships"),
            overall_reading=reading_data["overall_reading"],
            advice=reading_data["advice"],
            summary=reading_data["summary"],
        )

        db.add(reading_model)
        db.flush()  # Get ID without committing

        # Create ReadingCards
        for card_data in reading_data.get("cards", []):
            reading_card = ReadingCard(
                reading_id=reading_model.id,
                card_id=card_data["card_id"],
                position=card_data["position"],
                orientation=card_data["orientation"],
                interpretation=card_data["interpretation"],
                key_message=card_data["key_message"],
            )
            db.add(reading_card)

        db.commit()
        db.refresh(reading_model)

        return self._model_to_reading_dto(reading_model)

    async def get_reading_by_id(self, reading_id: str) -> Optional[ReadingDTO]:
        """ID로 리딩 조회"""
        db = self._get_session()
        reading_model = db.query(ReadingModel).filter(
            ReadingModel.id == reading_id
        ).first()

        if not reading_model:
            return None

        return self._model_to_reading_dto(reading_model)

    async def get_readings_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        spread_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[ReadingDTO]:
        """사용자별 리딩 목록 조회"""
        db = self._get_session()
        query = db.query(ReadingModel).filter(ReadingModel.user_id == user_id)

        # Apply filters
        if spread_type:
            query = query.filter(ReadingModel.spread_type == spread_type)
        if category:
            query = query.filter(ReadingModel.category == category)

        # Order by created_at descending
        query = query.order_by(ReadingModel.created_at.desc())

        # Apply pagination
        reading_models = query.offset(skip).limit(limit).all()
        return [self._model_to_reading_dto(reading) for reading in reading_models]

    async def get_total_readings_count(
        self,
        user_id: str,
        spread_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """사용자별 전체 리딩 수 조회"""
        db = self._get_session()
        query = db.query(func.count(ReadingModel.id)).filter(
            ReadingModel.user_id == user_id
        )

        # Apply filters
        if spread_type:
            query = query.filter(ReadingModel.spread_type == spread_type)
        if category:
            query = query.filter(ReadingModel.category == category)

        return query.scalar()

    async def update_reading(self, reading_id: str, reading_data: Dict[str, Any]) -> ReadingDTO:
        """리딩 수정"""
        db = self._get_session()
        reading_model = db.query(ReadingModel).filter(
            ReadingModel.id == reading_id
        ).first()

        if not reading_model:
            raise ValueError(f"Reading with id {reading_id} not found")

        # Update fields
        for key, value in reading_data.items():
            if key != "cards" and hasattr(reading_model, key):
                setattr(reading_model, key, value)

        db.commit()
        db.refresh(reading_model)

        return self._model_to_reading_dto(reading_model)

    async def delete_reading(self, reading_id: str) -> bool:
        """리딩 삭제"""
        db = self._get_session()
        reading_model = db.query(ReadingModel).filter(
            ReadingModel.id == reading_id
        ).first()

        if not reading_model:
            return False

        db.delete(reading_model)
        db.commit()
        return True

    # ==================== Connection Management ====================

    async def connect(self) -> None:
        """데이터베이스 연결"""
        # Session is created lazily, so just initialize
        self._session = SessionLocal()

    async def disconnect(self) -> None:
        """데이터베이스 연결 해제"""
        if self._session:
            self._session.close()
            self._session = None

    async def health_check(self) -> bool:
        """데이터베이스 상태 확인"""
        try:
            db = self._get_session()
            # Simple query to check connection
            db.execute("SELECT 1")
            return True
        except Exception:
            return False
