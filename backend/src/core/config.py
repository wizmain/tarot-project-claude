"""
애플리케이션 설정 관리 모듈

이 모듈의 목적:
- 환경 변수 기반 애플리케이션 설정 관리
- Pydantic을 활용한 타입 안전 설정
- .env 파일 자동 로드 및 검증
- 데이터베이스, Redis, AI API 키 등 모든 설정 중앙화

사용 예시:
    from src.core.config import settings
    print(settings.DATABASE_URL)
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스

    환경 변수에서 설정을 로드하여 타입 검증을 수행합니다.
    .env 파일이 있으면 자동으로 로드되며, 환경 변수가 우선합니다.
    """

    # Application
    APP_NAME: str = "Tarot AI Reading Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/tarot_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Authentication Provider
    AUTH_PRIMARY_PROVIDER: str = "firebase"  # firebase | custom_jwt | auth0
    AUTH_ENABLE_CUSTOM_JWT: bool = False

    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # AI Settings
    DEFAULT_AI_PROVIDER: str = "openai"  # openai, claude
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    AI_PROVIDER_PRIORITY: str = "openai,anthropic"

    # Email Configuration (for Custom JWT Provider)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@tarot-ai.com"
    SMTP_FROM_NAME: str = "Tarot AI"

    # Database Provider Selection
    DATABASE_PROVIDER: str = "firestore"  # firestore | postgresql

    # Firebase Configuration
    FIREBASE_API_KEY: Optional[str] = None  # Firebase Web API Key for REST API
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None  # Path to Firebase Admin SDK JSON file (optional)

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://tarot-frontend-414870328191.asia-northeast3.run.app",
        "https://tarot-aacbf.web.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        """Parse comma-separated CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
