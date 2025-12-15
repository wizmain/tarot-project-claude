"""
대화(Conversation) 데이터 모델 정의 모듈

이 모듈의 목적:
- 채팅 대화 세션의 데이터 구조 정의 (SQLAlchemy ORM)
- 사용자별 대화 이력 관리
- 대화 제목 및 메타데이터 저장

주요 모델:
- Conversation: 채팅 대화 세션 정보 (사용자, 제목, 생성 시간)

데이터베이스 관계:
- User 1 : N Conversation (One-to-Many)
- Conversation 1 : N Message (One-to-Many)

구현 사항:
- UUID 기반 Conversation ID (외부 노출, 예측 불가능)
- 인덱스를 통한 빠른 조회 (user_id, created_at)
- Cascade로 Conversation 삭제 시 관련 Message 자동 삭제

사용 예시:
    from src.models import Conversation
    from src.core.database import SessionLocal

    # Conversation 생성
    conversation = Conversation(
        user_id=user.id,
        title="타로 상담"
    )

    db.add(conversation)
    db.commit()
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.core.database import Base


class Conversation(Base):
    """
    채팅 대화 세션 모델

    사용자와 AI 간의 대화 세션을 저장합니다.
    하나의 대화는 여러 개의 메시지(Message)를 포함할 수 있습니다.

    주요 필드:
    - id: 고유 식별자 (UUID)
    - user_id: 사용자 ID
    - title: 대화 제목 (자동 생성 또는 사용자 지정)
    - created_at: 대화 생성 시간
    - updated_at: 마지막 업데이트 시간
    """

    __tablename__ = "conversations"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="대화 고유 ID (UUID)"
    )

    # User Relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )

    # Conversation Information
    title = Column(
        String(255),
        nullable=False,
        comment="대화 제목"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="대화 생성 시간"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 업데이트 시간"
    )

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Message.created_at",
        doc="대화의 메시지 목록"
    )

    user = relationship(
        "User",
        back_populates="conversations",
        doc="대화를 소유한 사용자"
    )

    # Indexes
    __table_args__ = (
        Index("idx_conversation_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title[:30]})>"

