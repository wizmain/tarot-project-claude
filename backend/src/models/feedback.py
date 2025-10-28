"""
타로 리딩 피드백 데이터 모델 정의 모듈

이 모듈의 목적:
- 타로 리딩에 대한 사용자 피드백 데이터 구조 정의 (SQLAlchemy ORM)
- 리딩 만족도, 정확도, 유용성 평가 저장
- 사용자 의견 및 개선사항 수집
- 피드백 분석 및 통계 지원

주요 모델:
- Feedback: 리딩에 대한 사용자 피드백 정보

데이터베이스 관계:
- Feedback N : 1 Reading (Many-to-One)
- Feedback N : 1 User (Many-to-One)

구현 사항:
- UUID 기반 Feedback ID
- 1-5 별점 평가 시스템
- boolean 필드로 유용성/정확성 평가
- 텍스트 코멘트 (선택사항)
- 중복 피드백 방지 (unique constraint on reading_id + user_id)
- 인덱스를 통한 빠른 조회 (reading_id, user_id, rating)

TASK 참조:
- TASK-035: Feedback 데이터 모델

사용 예시:
    from src.models import Feedback
    from src.core.database import SessionLocal

    # Feedback 생성
    feedback = Feedback(
        reading_id="uuid-of-reading",
        user_id="uuid-of-user",
        rating=5,
        comment="정말 도움이 되는 리딩이었습니다!",
        helpful=True,
        accurate=True
    )

    db = SessionLocal()
    db.add(feedback)
    db.commit()

저자: Claude Code (AI)
생성일: 2025-10-20
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.reading import Reading
    from src.models.user import User


class Feedback(Base):
    """
    타로 리딩 피드백 모델

    Attributes:
        id (UUID): 피드백 고유 식별자 (Primary Key)
        reading_id (UUID): 연관된 리딩 ID (Foreign Key to readings.id)
        user_id (UUID): 피드백 작성자 ID (Foreign Key to users.id)
        rating (int): 별점 평가 (1-5)
        comment (str | None): 사용자 코멘트 (선택사항, 최대 1000자)
        helpful (bool): 리딩이 유용했는지 여부
        accurate (bool): 리딩이 정확했는지 여부
        created_at (datetime): 피드백 생성 시각
        updated_at (datetime): 피드백 수정 시각

    Relationships:
        reading: 연관된 Reading 객체
        user: 피드백 작성자 User 객체

    Indexes:
        - (reading_id) for fast reading feedback lookup
        - (user_id) for user's feedback history
        - (rating) for statistics aggregation
        - (created_at) for chronological queries

    Constraints:
        - UNIQUE (reading_id, user_id) - 사용자당 리딩별 하나의 피드백만 허용
    """

    __tablename__ = "feedbacks"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="피드백 고유 식별자",
    )

    # Foreign Keys
    reading_id = Column(
        UUID(as_uuid=True),
        ForeignKey("readings.id", ondelete="CASCADE"),
        nullable=False,
        comment="연관된 리딩 ID",
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="피드백 작성자 ID",
    )

    # Rating and Feedback Fields
    rating = Column(
        Integer,
        nullable=False,
        comment="별점 평가 (1-5)",
    )

    comment = Column(
        Text,
        nullable=True,
        comment="사용자 코멘트 (선택사항)",
    )

    helpful = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="리딩이 유용했는지 여부",
    )

    accurate = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="리딩이 정확했는지 여부",
    )

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="피드백 생성 시각",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="피드백 수정 시각",
    )

    # Relationships
    reading = relationship(
        "Reading",
        back_populates="feedbacks",
        lazy="select",
    )

    user = relationship(
        "User",
        back_populates="feedbacks",
        lazy="select",
    )

    # Table constraints
    __table_args__ = (
        # Unique constraint: one feedback per user per reading
        UniqueConstraint(
            "reading_id",
            "user_id",
            name="uq_feedback_reading_user",
        ),
        # Indexes for performance
        {"comment": "타로 리딩 피드백 테이블"},
    )

    def __repr__(self) -> str:
        """String representation of Feedback"""
        return (
            f"<Feedback(id={self.id}, "
            f"reading_id={self.reading_id}, "
            f"user_id={self.user_id}, "
            f"rating={self.rating})>"
        )
