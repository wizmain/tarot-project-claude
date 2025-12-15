"""
사용자 데이터 모델 정의 모듈

이 모듈의 목적:
- 사용자 계정의 데이터 구조 정의 (SQLAlchemy ORM)
- 인증 Provider별 사용자 정보 관리
- 사용자 리딩 이력 관계 설정
- 사용자 프로필 및 메타데이터 저장

주요 모델:
- User: 사용자 계정 정보 (이메일, 이름, Provider 정보)

데이터베이스 관계:
- User 1 : N Reading (One-to-Many)

구현 사항:
- UUID 기반 User ID (외부 노출, 예측 불가능)
- Provider별 외부 ID 저장 (firebase_abc123, auth0_xyz789 등)
- JSON 타입으로 메타데이터 저장
- 인덱스를 통한 빠른 조회 (email, provider_user_id)
- Cascade로 User 삭제 시 관련 Reading은 유지 (nullable foreign key)

사용 예시:
    from src.models import User
    from src.core.database import SessionLocal

    # User 생성
    user = User(
        email="user@example.com",
        display_name="홍길동",
        provider_id="custom_jwt",
        provider_user_id="jwt_abc123",
        email_verified=True
    )

    db.add(user)
    db.commit()
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.core.database import Base


class User(Base):
    """
    사용자 계정 모델

    Attributes:
        id: 내부 UUID (Primary Key)
        email: 이메일 주소 (고유, 필수)
        display_name: 표시 이름
        photo_url: 프로필 사진 URL
        phone_number: 전화번호
        provider_id: 인증 Provider 식별자 (firebase, auth0, custom_jwt 등)
        provider_user_id: Provider의 사용자 ID (firebase_abc123 등)
        email_verified: 이메일 인증 여부
        is_active: 계정 활성화 여부
        is_superuser: 관리자 여부
        metadata: 추가 사용자 메타데이터 (JSON)
        created_at: 계정 생성 시간
        updated_at: 마지막 업데이트 시간
        last_login_at: 마지막 로그인 시간

    Relationships:
        readings: 사용자의 타로 리딩 이력 (One-to-Many)
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="사용자 고유 ID (UUID)"
    )

    # Basic Information
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="이메일 주소"
    )

    display_name = Column(
        String(100),
        nullable=True,
        comment="표시 이름"
    )

    photo_url = Column(
        String(500),
        nullable=True,
        comment="프로필 사진 URL"
    )

    phone_number = Column(
        String(20),
        nullable=True,
        comment="전화번호"
    )

    # Password (for custom_jwt provider)
    password_hash = Column(
        String(255),
        nullable=True,
        comment="비밀번호 해시 (custom_jwt provider용)"
    )

    # Provider Information
    provider_id = Column(
        String(50),
        nullable=False,
        index=True,
        comment="인증 Provider 식별자 (firebase, auth0, custom_jwt 등)"
    )

    provider_user_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Provider의 사용자 ID (firebase_abc123, auth0_xyz789 등)"
    )

    # Status Flags
    email_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="이메일 인증 여부"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="계정 활성화 여부"
    )

    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="관리자 여부"
    )

    # Metadata (user_metadata로 변경 - metadata는 SQLAlchemy 예약어)
    user_metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="추가 사용자 메타데이터 (JSON)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="계정 생성 시간"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 업데이트 시간"
    )

    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="마지막 로그인 시간"
    )

    # Relationships
    readings = relationship(
        "Reading",
        back_populates="user",
        cascade="save-update, merge",
        lazy="dynamic",
        doc="사용자의 타로 리딩 이력"
    )

    feedbacks = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="사용자가 작성한 피드백"
    )

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="사용자의 채팅 대화 목록"
    )

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_provider", "provider_id", "provider_user_id"),
        Index("idx_user_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, provider={self.provider_id})>"

    def to_dict(self) -> dict:
        """
        모델을 딕셔너리로 변환

        Returns:
            사용자 정보 딕셔너리
        """
        return {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "phone_number": self.phone_number,
            "provider_id": self.provider_id,
            "provider_user_id": self.provider_user_id,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "user_metadata": self.user_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
