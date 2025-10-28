"""
타로 리딩 데이터 모델 정의 모듈

이 모듈의 목적:
- 타로 리딩 세션의 데이터 구조 정의 (SQLAlchemy ORM)
- 리딩 결과 및 사용된 카드 정보 저장
- AI Provider 응답과 데이터베이스 간의 매핑
- 리딩 이력 관리 및 조회 지원

주요 모델:
- Reading: 타로 리딩 세션 정보 (질문, 응답, 메타데이터)
- ReadingCard: 리딩에 사용된 개별 카드 정보 (카드, 위치, 해석)

데이터베이스 관계:
- Reading 1 : N ReadingCard (One-to-Many)
- ReadingCard N : 1 Card (Many-to-One)
- Reading N : 1 User (Many-to-One, nullable for MVP)

구현 사항:
- UUID 기반 Reading ID (외부 노출, 예측 불가능)
- JSON 타입으로 advice 저장 (PostgreSQL 지원)
- Cascade delete로 Reading 삭제 시 관련 ReadingCard 자동 삭제
- 인덱스를 통한 빠른 조회 (user_id, created_at, spread_type)

TASK 참조:
- TASK-026: Reading 데이터 모델 설계

사용 예시:
    from src.models import Reading, ReadingCard
    from src.core.database import SessionLocal

    # Reading 생성
    reading = Reading(
        spread_type="one_card",
        question="새로운 직장으로 이직해야 할까요?",
        overall_reading="...",
        advice={
            "immediate_action": "...",
            "short_term": "...",
            ...
        },
        summary="..."
    )

    # ReadingCard 추가
    reading_card = ReadingCard(
        card_id=1,
        position="single",
        orientation="upright",
        interpretation="...",
        key_message="..."
    )
    reading.cards.append(reading_card)

    # 저장
    db.add(reading)
    db.commit()
"""
from datetime import datetime
from typing import List, Dict, Any
import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Reading(Base):
    """
    타로 리딩 세션 모델

    사용자의 질문과 AI가 생성한 타로 리딩 결과를 저장합니다.
    하나의 리딩은 여러 개의 카드(ReadingCard)를 포함할 수 있습니다.

    주요 필드:
    - id: 고유 식별자 (UUID)
    - user_id: 사용자 ID (nullable, User 모델 생성 후 연결)
    - spread_type: 스프레드 타입 (one_card, three_card_past_present_future, etc.)
    - question: 사용자의 질문
    - overall_reading: AI가 생성한 종합 리딩
    - advice: 조언 객체 (JSON)
    - summary: 한 줄 요약
    """
    __tablename__ = "readings"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # User (User 모델과 연결, nullable)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="사용자 ID"
    )

    # Reading 기본 정보
    spread_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="스프레드 타입 (one_card, three_card_past_present_future, etc.)"
    )
    question = Column(
        Text,
        nullable=False,
        comment="사용자의 질문"
    )
    category = Column(
        String(50),
        nullable=True,
        index=True,
        comment="리딩 카테고리 (love, career, finance, health, etc.)"
    )

    # AI 응답 결과 (ResponseParser 출력과 일치)
    card_relationships = Column(
        Text,
        nullable=True,
        comment="카드 간 관계 설명 (쓰리카드 이상에서 사용)"
    )
    overall_reading = Column(
        Text,
        nullable=False,
        comment="AI가 생성한 종합 리딩"
    )
    advice = Column(
        JSON,
        nullable=False,
        comment="조언 객체 (immediate_action, short_term, long_term, mindset, cautions)"
    )
    summary = Column(
        String(200),
        nullable=False,
        comment="한 줄 요약 메시지"
    )

    # 메타데이터
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="생성 시각"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 시각"
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="readings",
        doc="리딩을 수행한 사용자"
    )

    cards = relationship(
        "ReadingCard",
        back_populates="reading",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    feedbacks = relationship(
        "Feedback",
        back_populates="reading",
        cascade="all, delete-orphan",
        lazy="select",
        doc="이 리딩에 대한 피드백"
    )

    # Composite Indexes
    __table_args__ = (
        Index('idx_readings_user_created', 'user_id', 'created_at'),
        Index('idx_readings_spread_type', 'spread_type'),
        Index('idx_readings_created_at', 'created_at'),
    )

    def __repr__(self) -> str:
        """String representation of Reading"""
        return f"<Reading(id={self.id}, spread_type='{self.spread_type}', created_at={self.created_at})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Reading to dictionary representation

        Returns:
            Dictionary with all reading attributes including related cards
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "spread_type": self.spread_type,
            "question": self.question,
            "category": self.category,
            "cards": [card.to_dict() for card in self.cards] if self.cards else [],
            "card_relationships": self.card_relationships,
            "overall_reading": self.overall_reading,
            "advice": self.advice,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ReadingCard(Base):
    """
    리딩에 사용된 카드 모델

    Reading과 Card를 연결하는 중간 테이블 역할을 합니다.
    각 카드의 위치(position), 방향(orientation), AI 해석을 저장합니다.

    주요 필드:
    - reading_id: Reading 외래 키
    - card_id: Card 외래 키
    - position: 카드 위치 (past, present, future, single, etc.)
    - orientation: 카드 방향 (upright, reversed)
    - interpretation: AI가 생성한 카드 해석
    - key_message: 핵심 메시지
    """
    __tablename__ = "reading_cards"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    # Foreign Keys
    reading_id = Column(
        UUID(as_uuid=True),
        ForeignKey("readings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reading ID"
    )
    card_id = Column(
        Integer,
        ForeignKey("cards.id"),
        nullable=False,
        index=True,
        comment="Card ID"
    )

    # 카드 배치 정보
    position = Column(
        String(50),
        nullable=False,
        comment="카드 위치 (past, present, future, single, situation, action, outcome, etc.)"
    )
    orientation = Column(
        String(20),
        nullable=False,
        comment="카드 방향 (upright, reversed)"
    )

    # AI 해석 결과 (ResponseParser의 CardInterpretation과 일치)
    interpretation = Column(
        Text,
        nullable=False,
        comment="AI가 생성한 카드 해석"
    )
    key_message = Column(
        String(100),
        nullable=False,
        comment="핵심 메시지 한 줄"
    )

    # Relationships
    reading = relationship(
        "Reading",
        back_populates="cards"
    )
    card = relationship(
        "Card",
        lazy="joined"
    )

    # Composite Indexes
    __table_args__ = (
        Index('idx_reading_cards_reading', 'reading_id'),
        Index('idx_reading_cards_card', 'card_id'),
        Index('idx_reading_cards_reading_position', 'reading_id', 'position'),
    )

    def __repr__(self) -> str:
        """String representation of ReadingCard"""
        return (
            f"<ReadingCard(id={self.id}, "
            f"reading_id={self.reading_id}, "
            f"card_id={self.card_id}, "
            f"position='{self.position}', "
            f"orientation='{self.orientation}')>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ReadingCard to dictionary representation

        Returns:
            Dictionary with all reading card attributes
        """
        result = {
            "id": self.id,
            "reading_id": str(self.reading_id),
            "card_id": self.card_id,
            "position": self.position,
            "orientation": self.orientation,
            "interpretation": self.interpretation,
            "key_message": self.key_message,
        }

        # Card 정보 포함 (if loaded)
        if self.card:
            result["card"] = {
                "id": self.card.id,
                "name": self.card.name,
                "name_ko": self.card.name_ko,
                "arcana_type": self.card.arcana_type.value,
                "suit": self.card.suit.value if self.card.suit else None,
                "number": self.card.number,
                "keywords_upright": self.card.keywords_upright,
                "keywords_reversed": self.card.keywords_reversed,
                "meaning_upright": self.card.meaning_upright,
                "meaning_reversed": self.card.meaning_reversed,
                "description": self.card.description,
                "symbolism": self.card.symbolism,
                "image_url": self.card.image_url,
                "created_at": self.card.created_at.isoformat(),
                "updated_at": self.card.updated_at.isoformat(),
            }

        return result
