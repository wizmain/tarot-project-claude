"""
타로 카드 데이터 모델 정의 모듈

이 모듈의 목적:
- 타로 카드의 데이터 구조 정의 (SQLAlchemy ORM)
- 메이저/마이너 아르카나 구분
- 정방향/역방향 의미 저장
- 한국어 카드 데이터 지원

데이터베이스 스키마:
- 78장의 타로 카드 (메이저 22장 + 마이너 56장)
- 각 카드의 의미, 키워드, 이미지 정보
- 수트(Wands, Cups, Swords, Pentacles) 분류

TASK-009: 타로 카드 데이터 모델 설계 구현

사용 예시:
    card = Card(
        card_id="major_0",
        name="The Fool",
        arcana=ArcanaType.MAJOR,
        number=0,
        keywords=["new beginnings", "innocence"],
        upright_meaning="새로운 시작...",
        reversed_meaning="무모함..."
    )
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.sql import func
import enum

from src.core.database import Base


class ArcanaType(str, enum.Enum):
    """
    아르카나 타입 열거형

    타로 카드는 크게 메이저 아르카나(22장)와 마이너 아르카나(56장)로 구분됩니다.
    - MAJOR: 인생의 큰 주제와 영적 여정을 나타내는 카드
    - MINOR: 일상의 상황과 세부사항을 나타내는 카드
    """
    MAJOR = "major"  # 메이저 아르카나 (0-21번)
    MINOR = "minor"  # 마이너 아르카나 (각 수트당 14장)


class Suit(str, enum.Enum):
    """
    타로 수트 열거형 (마이너 아르카나 전용)

    마이너 아르카나 56장은 4개의 수트로 나뉩니다:
    - WANDS (완드/지팡이): 열정, 창의성, 에너지
    - CUPS (컵/성배): 감정, 관계, 직관
    - SWORDS (검): 생각, 갈등, 의사소통
    - PENTACLES (펜타클/동전): 물질, 재정, 실용성
    """
    WANDS = "wands"          # 완드 (불의 원소)
    CUPS = "cups"            # 컵 (물의 원소)
    SWORDS = "swords"        # 검 (공기의 원소)
    PENTACLES = "pentacles"  # 펜타클 (흙의 원소)


class Card(Base):
    """
    타로 카드 모델

    데이터베이스에 저장되는 타로 카드 정보를 정의합니다.
    78장의 타로 카드 각각의 의미, 상징, 이미지 등을 포함합니다.

    주요 필드:
    - card_id: 고유 식별자 (예: "major_0", "wands_01")
    - name: 카드 이름 (예: "The Fool", "Ace of Wands")
    - arcana: 메이저/마이너 아르카나 구분
    - suit: 수트 (마이너 아르카나만 해당)
    - keywords: 카드를 대표하는 키워드 리스트
    - upright_meaning: 정방향 의미 (한국어)
    - reversed_meaning: 역방향 의미 (한국어)
    """
    __tablename__ = "cards"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Card identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    name_ko = Column(String(100), nullable=False)
    number = Column(Integer, nullable=True)  # 0-21 for Major, 1-14 for Minor, null for Court cards

    # Card type
    arcana_type = Column(Enum(ArcanaType), nullable=False, index=True)
    suit = Column(Enum(Suit), nullable=True)  # Only for Minor Arcana

    # Card meanings
    keywords_upright = Column(JSON, nullable=False)  # List of upright keywords
    keywords_reversed = Column(JSON, nullable=False)  # List of reversed keywords
    meaning_upright = Column(Text, nullable=False)  # Detailed upright meaning
    meaning_reversed = Column(Text, nullable=False)  # Detailed reversed meaning

    # Additional descriptions
    description = Column(Text, nullable=True)  # General card description
    symbolism = Column(Text, nullable=True)  # Symbolic interpretation

    # Image reference
    image_url = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_arcana_suit', 'arcana_type', 'suit'),
        Index('idx_name_search', 'name', 'name_ko'),
    )

    def __repr__(self) -> str:
        """String representation of Card"""
        return f"<Card(id={self.id}, name='{self.name}', arcana={self.arcana_type.value})>"

    def to_dict(self) -> dict:
        """
        Convert card to dictionary representation

        Returns:
            Dictionary with all card attributes
        """
        return {
            "id": self.id,
            "name": self.name,
            "name_ko": self.name_ko,
            "number": self.number,
            "arcana_type": self.arcana_type.value,
            "suit": self.suit.value if self.suit else None,
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
