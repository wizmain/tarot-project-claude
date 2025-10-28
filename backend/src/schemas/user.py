"""
사용자 Pydantic 스키마 정의 모듈

이 모듈의 목적:
- API 요청/응답에 사용할 사용자 데이터 검증 스키마
- 데이터베이스 모델과 API 간의 변환
- 입력 데이터 유효성 검사

주요 스키마:
- UserBase: 기본 사용자 정보
- UserCreate: 사용자 생성 요청
- UserUpdate: 사용자 수정 요청
- UserInDB: 데이터베이스에 저장된 사용자 (전체 정보)
- UserResponse: API 응답용 사용자 정보

사용 예시:
    # 사용자 생성 요청
    user_data = UserCreate(
        email="user@example.com",
        display_name="홍길동",
        provider_id="custom_jwt",
        provider_user_id="jwt_abc123"
    )

    # 응답
    response = UserResponse.from_orm(db_user)
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """
    사용자 기본 스키마
    """
    email: EmailStr = Field(..., description="이메일 주소")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    photo_url: Optional[str] = Field(None, max_length=500, description="프로필 사진 URL")
    phone_number: Optional[str] = Field(None, max_length=20, description="전화번호")

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """
    사용자 생성 요청 스키마
    """
    provider_id: str = Field(..., max_length=50, description="인증 Provider 식별자")
    provider_user_id: str = Field(..., max_length=255, description="Provider의 사용자 ID")
    email_verified: bool = Field(default=False, description="이메일 인증 여부")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "display_name": "홍길동",
                "photo_url": "https://example.com/photo.jpg",
                "phone_number": "+821012345678",
                "provider_id": "custom_jwt",
                "provider_user_id": "jwt_abc123",
                "email_verified": True,
                "metadata": {
                    "referral_code": "ABC123"
                }
            }
        }


class UserUpdate(BaseModel):
    """
    사용자 수정 요청 스키마
    """
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    photo_url: Optional[str] = Field(None, max_length=500, description="프로필 사진 URL")
    phone_number: Optional[str] = Field(None, max_length=20, description="전화번호")
    email_verified: Optional[bool] = Field(None, description="이메일 인증 여부")
    is_active: Optional[bool] = Field(None, description="계정 활성화 여부")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "display_name": "김철수",
                "photo_url": "https://example.com/new-photo.jpg",
                "email_verified": True
            }
        }


class UserInDB(UserBase):
    """
    데이터베이스에 저장된 사용자 스키마 (전체 정보)
    """
    id: UUID = Field(..., description="사용자 고유 ID")
    provider_id: str = Field(..., description="인증 Provider 식별자")
    provider_user_id: str = Field(..., description="Provider의 사용자 ID")
    email_verified: bool = Field(..., description="이메일 인증 여부")
    is_active: bool = Field(..., description="계정 활성화 여부")
    is_superuser: bool = Field(..., description="관리자 여부")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    created_at: datetime = Field(..., description="계정 생성 시간")
    updated_at: datetime = Field(..., description="마지막 업데이트 시간")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class UserResponse(BaseModel):
    """
    API 응답용 사용자 스키마
    """
    id: UUID = Field(..., description="사용자 고유 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    display_name: Optional[str] = Field(None, description="표시 이름")
    photo_url: Optional[str] = Field(None, description="프로필 사진 URL")
    phone_number: Optional[str] = Field(None, description="전화번호")
    provider_id: str = Field(..., description="인증 Provider 식별자")
    email_verified: bool = Field(..., description="이메일 인증 여부")
    is_active: bool = Field(..., description="계정 활성화 여부")
    created_at: datetime = Field(..., description="계정 생성 시간")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "display_name": "홍길동",
                "photo_url": "https://example.com/photo.jpg",
                "phone_number": "+821012345678",
                "provider_id": "custom_jwt",
                "email_verified": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-15T10:30:00Z"
            }
        }


class UserWithStats(UserResponse):
    """
    통계 정보를 포함한 사용자 스키마
    """
    total_readings: int = Field(default=0, description="총 리딩 횟수")
    recent_readings: int = Field(default=0, description="최근 30일 리딩 횟수")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "display_name": "홍길동",
                "photo_url": "https://example.com/photo.jpg",
                "phone_number": "+821012345678",
                "provider_id": "custom_jwt",
                "email_verified": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-15T10:30:00Z",
                "total_readings": 42,
                "recent_readings": 7
            }
        }


# Auth 관련 스키마
class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=6, description="비밀번호")
    provider: Optional[str] = Field(None, description="특정 Provider 지정 (선택사항)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }


class SignUpRequest(BaseModel):
    """회원가입 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=6, description="비밀번호")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    provider: Optional[str] = Field(None, description="특정 Provider 지정 (선택사항)")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """비밀번호 강도 검증"""
        if len(v) < 6:
            raise ValueError('비밀번호는 최소 6자 이상이어야 합니다')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@example.com",
                "password": "securePassword123!",
                "display_name": "새로운 사용자"
            }
        }


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: Optional[str] = Field(None, description="리프레시 토큰")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")
    user: UserResponse = Field(..., description="사용자 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "display_name": "홍길동",
                    "provider_id": "custom_jwt",
                    "email_verified": True,
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_login_at": "2024-01-15T10:30:00Z"
                }
            }
        }


class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인 스키마"""
    reset_token: str = Field(..., description="비밀번호 재설정 토큰")
    new_password: str = Field(..., min_length=6, description="새 비밀번호")

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """비밀번호 강도 검증"""
        if len(v) < 6:
            raise ValueError('비밀번호는 최소 6자 이상이어야 합니다')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "newSecurePassword123!"
            }
        }
