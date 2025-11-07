"""
Auth Provider Models

인증 관련 데이터 모델 및 예외 정의
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    """사용자 프로필 정보"""
    uid: str = Field(..., description="사용자 고유 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    email_verified: bool = Field(default=False, description="이메일 인증 여부")
    display_name: Optional[str] = Field(None, description="표시 이름")
    photo_url: Optional[str] = Field(None, description="프로필 사진 URL")
    phone_number: Optional[str] = Field(None, description="전화번호")
    provider_id: str = Field(..., description="인증 제공자 ID")
    created_at: Optional[datetime] = Field(None, description="계정 생성 시간")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    class Config:
        json_json_schema_extra = {
            "example": {
                "uid": "firebase_abc123",
                "email": "user@example.com",
                "email_verified": True,
                "display_name": "홍길동",
                "provider_id": "firebase"
            }
        }


class AuthTokens(BaseModel):
    """인증 토큰"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: Optional[str] = Field(None, description="리프레시 토큰")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")

    class Config:
        json_json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }


class AuthResponse(BaseModel):
    """인증 응답"""
    user: UserProfile = Field(..., description="사용자 프로필")
    tokens: AuthTokens = Field(..., description="인증 토큰")
    is_new_user: bool = Field(default=False, description="신규 사용자 여부")
    provider: str = Field(..., description="인증 제공자")

    class Config:
        json_json_schema_extra = {
            "example": {
                "user": {
                    "uid": "firebase_abc123",
                    "email": "user@example.com",
                    "email_verified": True,
                    "display_name": "홍길동",
                    "provider_id": "firebase"
                },
                "tokens": {
                    "access_token": "eyJhbGci...",
                    "refresh_token": "eyJhbGci...",
                    "token_type": "Bearer",
                    "expires_in": 3600
                },
                "is_new_user": False,
                "provider": "firebase"
            }
        }


class TokenVerificationResult(BaseModel):
    """토큰 검증 결과"""
    valid: bool = Field(..., description="토큰 유효성")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    email: Optional[EmailStr] = Field(None, description="이메일")
    claims: Dict[str, Any] = Field(default_factory=dict, description="토큰 클레임")
    error: Optional[str] = Field(None, description="에러 메시지")
    provider: Optional[str] = Field(None, description="토큰을 검증한 Provider ID")


# Auth Exceptions
class AuthProviderError(Exception):
    """Auth Provider 기본 에러"""
    def __init__(
        self,
        message: str,
        provider: str,
        error_type: str = "UNKNOWN_ERROR",
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.provider = provider
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)


class AuthInvalidCredentialsError(AuthProviderError):
    """잘못된 인증 정보 에러"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="INVALID_CREDENTIALS",
            original_error=original_error
        )


class AuthUserNotFoundError(AuthProviderError):
    """사용자를 찾을 수 없음 에러"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="USER_NOT_FOUND",
            original_error=original_error
        )


class AuthEmailAlreadyExistsError(AuthProviderError):
    """이메일 중복 에러"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="EMAIL_ALREADY_EXISTS",
            original_error=original_error
        )


class AuthWeakPasswordError(AuthProviderError):
    """약한 비밀번호 에러"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="WEAK_PASSWORD",
            original_error=original_error
        )


class AuthInvalidTokenError(AuthProviderError):
    """유효하지 않은 토큰 에러"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="INVALID_TOKEN",
            original_error=original_error
        )


class AuthTokenExpiredError(AuthProviderError):
    """만료된 토큰 에러"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="TOKEN_EXPIRED",
            original_error=original_error
        )


class AuthServiceUnavailableError(AuthProviderError):
    """서비스 사용 불가 에러"""
    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            provider=provider,
            error_type="SERVICE_UNAVAILABLE",
            original_error=original_error
        )
        self.retry_after = retry_after
