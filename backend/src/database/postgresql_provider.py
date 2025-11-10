"""
PostgreSQL Database Provider

기존 SQLAlchemy 모델을 사용하는 DatabaseProvider 구현체
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, cast, Integer
import random

from .provider import (
    DatabaseProvider,
    Card as CardDTO,
    Reading as ReadingDTO,
    Feedback as FeedbackDTO,
)
from src.core.database import SessionLocal
from src.models.card import Card as CardModel, ArcanaType, Suit
from src.models.reading import Reading as ReadingModel, ReadingCard
from src.models.feedback import Feedback as FeedbackModel
from src.models.user import User as UserModel


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
            meaning_upright=card_model.meaning_upright,
            meaning_reversed=card_model.meaning_reversed,
            description=card_model.description,
            symbolism=card_model.symbolism,
            image_url=card_model.image_url,
            created_at=card_model.created_at,
            updated_at=card_model.updated_at,
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
                    "keywords_upright": reading_card.card.keywords_upright,
                    "keywords_reversed": reading_card.card.keywords_reversed,
                    "meaning_upright": reading_card.card.meaning_upright,
                    "meaning_reversed": reading_card.card.meaning_reversed,
                    "description": reading_card.card.description,
                    "symbolism": reading_card.card.symbolism,
                    "image_url": reading_card.card.image_url,
                    "created_at": reading_card.card.created_at,
                    "updated_at": reading_card.card.updated_at,
                }
            }
            cards.append(card_data)

        return ReadingDTO(
            id=str(reading_model.id),
            user_id=str(reading_model.user_id) if reading_model.user_id else "anonymous",
            question=reading_model.question,
            spread_type=reading_model.spread_type,
            category=reading_model.category,
            cards=cards,
            card_relationships=reading_model.card_relationships,
            overall_reading=reading_model.overall_reading,
            advice=reading_model.advice,
            summary=reading_model.summary,
            created_at=reading_model.created_at,
            updated_at=reading_model.updated_at,
        )

    def _model_to_feedback_dto(self, feedback_model: FeedbackModel) -> FeedbackDTO:
        """Convert SQLAlchemy Feedback model to Feedback DTO"""
        return FeedbackDTO(
            id=str(feedback_model.id),
            reading_id=str(feedback_model.reading_id),
            user_id=str(feedback_model.user_id),
            rating=feedback_model.rating,
            comment=feedback_model.comment,
            helpful=feedback_model.helpful,
            accurate=feedback_model.accurate,
            created_at=feedback_model.created_at,
            updated_at=feedback_model.updated_at,
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
            description=card_data.get("description"),
            symbolism=card_data.get("symbolism"),
            image_url=card_data.get("image_url"),
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

    # ==================== Feedback Operations ====================

    async def create_feedback(self, feedback_data: Dict[str, Any]) -> FeedbackDTO:
        """피드백 생성"""
        db = self._get_session()

        feedback_model = FeedbackModel(
            id=uuid.UUID(feedback_data['id']) if feedback_data.get('id') else uuid.uuid4(),
            reading_id=uuid.UUID(feedback_data['reading_id']),
            user_id=uuid.UUID(feedback_data['user_id']),
            rating=feedback_data['rating'],
            comment=feedback_data.get('comment'),
            helpful=feedback_data.get('helpful', True),
            accurate=feedback_data.get('accurate', True),
        )

        db.add(feedback_model)
        db.commit()
        db.refresh(feedback_model)

        return self._model_to_feedback_dto(feedback_model)

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackDTO]:
        """ID로 피드백 조회"""
        db = self._get_session()
        feedback = db.query(FeedbackModel).filter(
            FeedbackModel.id == uuid.UUID(feedback_id)
        ).first()
        return self._model_to_feedback_dto(feedback) if feedback else None

    async def get_feedback_by_reading(
        self,
        reading_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[FeedbackDTO]:
        """특정 리딩의 피드백 목록 조회"""
        db = self._get_session()
        feedback_models = (
            db.query(FeedbackModel)
            .filter(FeedbackModel.reading_id == uuid.UUID(reading_id))
            .order_by(FeedbackModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._model_to_feedback_dto(feedback) for feedback in feedback_models]

    async def get_feedback_by_reading_and_user(
        self,
        reading_id: str,
        user_id: str,
    ) -> Optional[FeedbackDTO]:
        """리딩과 사용자 조합으로 피드백 조회"""
        db = self._get_session()
        feedback = (
            db.query(FeedbackModel)
            .filter(
                FeedbackModel.reading_id == uuid.UUID(reading_id),
                FeedbackModel.user_id == uuid.UUID(user_id),
            )
            .first()
        )
        return self._model_to_feedback_dto(feedback) if feedback else None

    async def update_feedback(
        self,
        feedback_id: str,
        feedback_data: Dict[str, Any],
    ) -> Optional[FeedbackDTO]:
        """피드백 수정"""
        db = self._get_session()
        feedback = db.query(FeedbackModel).filter(
            FeedbackModel.id == uuid.UUID(feedback_id)
        ).first()

        if not feedback:
            return None

        for field in ("rating", "comment", "helpful", "accurate"):
            if field in feedback_data and feedback_data[field] is not None:
                setattr(feedback, field, feedback_data[field])

        db.commit()
        db.refresh(feedback)

        return self._model_to_feedback_dto(feedback)

    async def delete_feedback(self, feedback_id: str) -> bool:
        """피드백 삭제"""
        db = self._get_session()
        feedback = db.query(FeedbackModel).filter(
            FeedbackModel.id == uuid.UUID(feedback_id)
        ).first()

        if not feedback:
            return False

        db.delete(feedback)
        db.commit()
        return True

    async def get_feedback_statistics(self) -> Dict[str, Any]:
        """전체 피드백 통계"""
        db = self._get_session()

        stats_query = db.query(
            func.count(FeedbackModel.id).label("total_count"),
            func.avg(FeedbackModel.rating).label("avg_rating"),
            func.sum(cast(FeedbackModel.helpful, Integer)).label("helpful_count"),
            func.sum(cast(FeedbackModel.accurate, Integer)).label("accurate_count"),
        ).first()

        total_count = stats_query.total_count or 0
        avg_rating = float(stats_query.avg_rating) if stats_query.avg_rating else 0.0
        helpful_count = stats_query.helpful_count or 0
        accurate_count = stats_query.accurate_count or 0

        return {
            "total_feedback_count": total_count,
            "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
            "helpful_count": helpful_count,
            "accurate_count": accurate_count,
            "helpful_rate": round((helpful_count / total_count * 100), 1) if total_count else 0.0,
            "accurate_rate": round((accurate_count / total_count * 100), 1) if total_count else 0.0,
        }

    async def get_feedback_statistics_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """기간별 피드백 통계"""
        db = self._get_session()

        stats_query = db.query(
            func.count(FeedbackModel.id).label("total_count"),
            func.avg(FeedbackModel.rating).label("avg_rating"),
            func.sum(cast(FeedbackModel.helpful, Integer)).label("helpful_count"),
            func.sum(cast(FeedbackModel.accurate, Integer)).label("accurate_count"),
        ).filter(
            and_(
                FeedbackModel.created_at >= start_date,
                FeedbackModel.created_at < end_date,
            )
        ).first()

        total_count = stats_query.total_count or 0
        avg_rating = float(stats_query.avg_rating) if stats_query.avg_rating else 0.0
        helpful_count = stats_query.helpful_count or 0
        accurate_count = stats_query.accurate_count or 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_feedback_count": total_count,
            "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
            "helpful_count": helpful_count,
            "accurate_count": accurate_count,
            "helpful_rate": round((helpful_count / total_count * 100), 1) if total_count else 0.0,
            "accurate_rate": round((accurate_count / total_count * 100), 1) if total_count else 0.0,
        }

    async def get_feedback_statistics_by_spread_type(self) -> List[Dict[str, Any]]:
        """스프레드 타입별 피드백 통계"""
        db = self._get_session()

        stats = db.query(
            ReadingModel.spread_type,
            func.count(FeedbackModel.id).label("feedback_count"),
            func.avg(FeedbackModel.rating).label("avg_rating"),
            func.sum(cast(FeedbackModel.helpful, Integer)).label("helpful_count"),
            func.sum(cast(FeedbackModel.accurate, Integer)).label("accurate_count"),
        ).join(
            FeedbackModel, ReadingModel.id == FeedbackModel.reading_id
        ).group_by(
            ReadingModel.spread_type
        ).all()

        results: List[Dict[str, Any]] = []
        for stat in stats:
            total_count = stat.feedback_count or 0
            avg_rating = float(stat.avg_rating) if stat.avg_rating else 0.0
            helpful_count = stat.helpful_count or 0
            accurate_count = stat.accurate_count or 0

            results.append({
                "spread_type": stat.spread_type,
                "feedback_count": total_count,
                "average_rating": round(avg_rating, 2) if avg_rating else 0.0,
                "helpful_count": helpful_count,
                "accurate_count": accurate_count,
                "helpful_rate": round((helpful_count / total_count * 100), 1) if total_count else 0.0,
                "accurate_rate": round((accurate_count / total_count * 100), 1) if total_count else 0.0,
            })

        return results

    # ==================== Admin Statistics Operations ====================

    async def get_total_users_count(self) -> int:
        """전체 사용자 수 조회 (관리자 대시보드용)"""
        db = self._get_session()
        count = db.query(func.count(UserModel.id)).scalar()
        return count or 0

    async def get_total_readings_count_all(self) -> int:
        """전체 리딩 수 조회 (관리자 대시보드용, user_id 필터 없음)"""
        db = self._get_session()
        count = db.query(func.count(ReadingModel.id)).scalar()
        return count or 0

    async def get_readings_count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """기간별 리딩 수 조회 (관리자 대시보드용)"""
        db = self._get_session()
        count = db.query(func.count(ReadingModel.id)).filter(
            and_(
                ReadingModel.created_at >= start_date,
                ReadingModel.created_at < end_date
            )
        ).scalar()
        return count or 0

    async def get_total_llm_cost(self) -> float:
        """전체 LLM 비용 합계 조회 (관리자 대시보드용)"""
        db = self._get_session()
        readings = db.query(ReadingModel.llm_usage).all()
        total_cost = 0.0

        for reading in readings:
            llm_usage = reading.llm_usage if reading.llm_usage else []
            if isinstance(llm_usage, list):
                for log in llm_usage:
                    if isinstance(log, dict):
                        cost = log.get('estimated_cost', 0.0)
                        if isinstance(cost, (int, float)):
                            total_cost += cost

        return round(total_cost, 2)

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
