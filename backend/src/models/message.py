"""
메시지(Message) 데이터 모델 정의 모듈

이 모듈의 목적:
- 채팅 메시지의 데이터 구조 정의 (SQLAlchemy ORM)
- 사용자와 AI 간의 메시지 교환 저장
- 메시지 역할(role) 및 메타데이터 관리

주요 모델:
- Message: 채팅 메시지 정보 (대화, 역할, 내용, 메타데이터)

데이터베이스 관계:
- Conversation 1 : N Message (One-to-Many)
- Message N : 1 Conversation (Many-to-One)

구현 사항:
- UUID 기반 Message ID (외부 노출, 예측 불가능)
- role 필드로 사용자/AI 구분 (user, assistant, system)
- JSON 타입으로 메타데이터 저장 (타로 리딩 정보 등)
- 인덱스를 통한 빠른 조회 (conversation_id, created_at)

사용 예시:
    from src.models import Message
    from src.core.database import SessionLocal

    # Message 생성
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="안녕하세요"
    )

    db.add(message)
    db.commit()
"""
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from src.core.database import Base


class MessageRole(str, enum.Enum):
    """메시지 역할 열거형"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """
    채팅 메시지 모델

    사용자와 AI 간의 개별 메시지를 저장합니다.
    메시지는 특정 대화(Conversation)에 속합니다.

    주요 필드:
    - id: 고유 식별자 (UUID)
    - conversation_id: 대화 ID
    - role: 메시지 역할 (user, assistant, system)
    - content: 메시지 내용
    - metadata: 추가 메타데이터 (JSON) - 타로 리딩 정보 등
    - created_at: 메시지 생성 시간
    """

    __tablename__ = "messages"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="메시지 고유 ID (UUID)"
    )

    # Conversation Relationship
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="대화 ID"
    )

    # Message Content
    role = Column(
        Enum(MessageRole),
        nullable=False,
        comment="메시지 역할 (user, assistant, system)"
    )

    content = Column(
        Text,
        nullable=False,
        comment="메시지 내용"
    )

    # Metadata (타로 리딩 정보, 카드 선택 등)
    message_metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="추가 메타데이터 (JSON)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="메시지 생성 시간"
    )

    # Relationships
    conversation = relationship(
        "Conversation",
        back_populates="messages",
        doc="메시지가 속한 대화"
    )

    # Indexes
    __table_args__ = (
        Index("idx_message_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role}, content={self.content[:30]})>"

