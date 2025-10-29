"""
Auth Dependencies - 인증 관련 FastAPI 의존성

이 모듈의 목적:
- JWT 토큰 검증 및 현재 사용자 조회
- FastAPI의 Depends를 사용한 의존성 주입
- 인증이 필요한 엔드포인트에서 재사용

주요 기능:
- get_current_user(): 현재 로그인한 사용자 조회 (토큰 검증)
- get_current_active_user(): 활성화된 사용자만 허용
- get_current_superuser(): 관리자 사용자만 허용
- get_auth_orchestrator(): Auth Orchestrator 싱글톤 인스턴스

사용 예시:
    from fastapi import APIRouter, Depends
    from src.api.dependencies.auth import get_current_user
    from src.models import User

    router = APIRouter()

    @router.get("/me")
    async def get_me(current_user: User = Depends(get_current_user)):
        return current_user.to_dict()
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.database import get_db_optional
from src.core.config import settings
from src.core.logging import get_logger
from src.auth import AuthOrchestrator
from src.auth.models import AuthInvalidTokenError
from src.api.repositories.user_repository import UserRepository
from src.models import User

logger = get_logger(__name__)

# HTTP Bearer 토큰 스키마 (Authorization: Bearer <token>)
security = HTTPBearer()

# Auth Orchestrator 싱글톤
_auth_orchestrator = None

SQL_BACKEND_ENABLED = getattr(settings, "DATABASE_PROVIDER", "postgresql").lower() != "firestore"


@dataclass
class FirebaseUser:
    """Firebase 인증 사용자를 표현하는 경량 객체"""
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    email_verified: bool = False
    is_active: bool = True
    is_superuser: bool = False
    provider_id: str = "firebase"
    user_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.provider_user_id = self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "email_verified": self.email_verified,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "provider_id": self.provider_id,
            "provider_user_id": self.provider_user_id,
            "user_metadata": self.user_metadata,
        }


def _build_firebase_user(verification_result) -> FirebaseUser:
    """Firebase 토큰 검증 결과를 FirebaseUser 객체로 변환"""
    claims = getattr(verification_result, "claims", {}) or {}
    email = claims.get("email") or getattr(verification_result, "email", None)
    display_name = claims.get("name") or claims.get("display_name")
    photo_url = claims.get("picture")
    email_verified = claims.get("email_verified", False)
    is_superuser = bool(claims.get("admin") or claims.get("is_superuser"))

    metadata = {
        "provider": getattr(verification_result, "provider", "firebase"),
        "auth_time": claims.get("auth_time"),
    }

    user = FirebaseUser(
        id=verification_result.user_id,
        email=email,
        display_name=display_name,
        photo_url=photo_url,
        email_verified=email_verified,
        is_superuser=is_superuser,
        user_metadata={k: v for k, v in metadata.items() if v is not None},
    )

    return user


def get_auth_orchestrator() -> AuthOrchestrator:
    """
    Auth Orchestrator 싱글톤 인스턴스 반환

    Returns:
        AuthOrchestrator: 초기화된 Auth Orchestrator

    Raises:
        ValueError: Auth Provider가 설정되지 않은 경우
    """
    global _auth_orchestrator

    if _auth_orchestrator is None:
        # Primary Provider 설정 (환경 변수에서 읽기, 기본값: custom_jwt)
        primary_provider = getattr(settings, 'AUTH_PRIMARY_PROVIDER', 'firebase')

        # Provider 설정
        configs = {}

        # Custom JWT Provider 설정 (선택적)
        if settings.AUTH_ENABLE_CUSTOM_JWT or primary_provider == 'custom_jwt':
            configs['custom_jwt'] = {
                'secret_key': settings.SECRET_KEY,
                'algorithm': 'HS256',
                'access_token_expire_minutes': 60,
                'refresh_token_expire_days': 7,
            }

        # Firebase Provider 설정 (선택적)
        firebase_config = {}
        if getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None):
            firebase_config['credentials_path'] = settings.FIREBASE_CREDENTIALS_PATH
        if getattr(settings, 'FIREBASE_API_KEY', None):
            firebase_config['api_key'] = settings.FIREBASE_API_KEY
        if firebase_config:
            configs['firebase'] = firebase_config

        # Auth0 Provider 설정 (선택적)
        if hasattr(settings, 'AUTH0_DOMAIN') and hasattr(settings, 'AUTH0_CLIENT_ID'):
            configs['auth0'] = {
                'domain': settings.AUTH0_DOMAIN,
                'client_id': settings.AUTH0_CLIENT_ID,
                'client_secret': getattr(settings, 'AUTH0_CLIENT_SECRET', None),
            }

        # Fallback providers
        fallback_providers = [
            provider_name
            for provider_name in configs.keys()
            if provider_name != primary_provider
        ]

        try:
            _auth_orchestrator = AuthOrchestrator(
                primary_provider=primary_provider,
                fallback_providers=fallback_providers or None,
                configs=configs,
                enable_fallback=True
            )
            logger.info(
                f"Auth Orchestrator initialized: "
                f"primary={primary_provider}, fallback={fallback_providers}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Auth Orchestrator: {e}")
            raise ValueError(f"Auth Provider 초기화 실패: {e}")

    return _auth_orchestrator


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Optional[Session] = Depends(get_db_optional),
) -> User:
    """
    현재 로그인한 사용자 조회 (JWT 토큰 검증)

    Authorization 헤더에서 Bearer 토큰을 추출하고,
    Auth Provider를 통해 검증한 후 사용자를 반환합니다.

    Args:
        credentials: HTTP Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User: 인증된 사용자 객체

    Raises:
        HTTPException 401: 토큰이 유효하지 않거나 사용자를 찾을 수 없음
        HTTPException 500: 서버 에러
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Bearer 토큰 추출
        token = credentials.credentials

        # Auth Orchestrator를 통해 토큰 검증
        orchestrator = get_auth_orchestrator()
        verification_result = await orchestrator.verify_token(token)

        if not verification_result.valid:
            logger.warning(f"[Auth] 토큰 검증 실패: {verification_result.error}")
            raise credentials_exception

        # Provider User ID로 사용자 조회
        # verification_result.provider를 사용하여 실제 provider 확인
        provider_id = (
            verification_result.provider
            if hasattr(verification_result, "provider")
            else orchestrator.primary_provider_name
        )

        # Provider에 따라 provider_user_id 형식 결정
        if provider_id == "firebase":
            provider_user_id = verification_result.user_id
        else:
            provider_user_id = f"jwt_{verification_result.user_id}"

        if not SQL_BACKEND_ENABLED or db is None:
            firebase_user = _build_firebase_user(verification_result)
            logger.info(
                "[Auth] Firebase 사용자 인증 성공: uid=%s email=%s",
                firebase_user.id,
                firebase_user.email,
            )
            return firebase_user

        user = UserRepository.get_by_provider(
            db=db,
            provider_id=provider_id,
            provider_user_id=provider_user_id
        )

        if not user:
            # Firebase 사용자인 경우 자동으로 DB에 생성 또는 기존 사용자에 링크
            if provider_id == 'firebase':
                # Firebase 토큰에서 사용자 정보 추출
                email = verification_result.claims.get('email') if hasattr(verification_result, 'claims') else None
                display_name = verification_result.claims.get('name') if hasattr(verification_result, 'claims') else None
                photo_url = verification_result.claims.get('picture') if hasattr(verification_result, 'claims') else None
                email_verified = verification_result.claims.get('email_verified', False) if hasattr(verification_result, 'claims') else False

                # 먼저 이메일로 기존 사용자 찾기
                existing_user = UserRepository.get_by_email(db=db, email=email) if email else None

                if existing_user:
                    # 기존 사용자에 Firebase 프로바이더 정보 추가
                    logger.info(
                        f"[Auth] 기존 사용자에 Firebase 프로바이더 연결: "
                        f"user_id={existing_user.id}, email={email}, "
                        f"firebase_uid={provider_user_id}"
                    )

                    # 프로바이더 정보 업데이트
                    existing_user.provider_id = provider_id
                    existing_user.provider_user_id = provider_user_id

                    # Firebase 정보로 업데이트 (더 최신 정보일 수 있음)
                    if display_name:
                        existing_user.display_name = display_name
                    if photo_url:
                        existing_user.photo_url = photo_url
                    if email_verified:
                        existing_user.email_verified = email_verified

                    db.commit()
                    db.refresh(existing_user)
                    user = existing_user
                    logger.info(f"[Auth] Firebase 프로바이더 연결 완료: user_id={user.id}")
                else:
                    # 새로운 사용자 생성
                    logger.info(
                        f"[Auth] Firebase 사용자 자동 생성: "
                        f"provider_user_id={provider_user_id}"
                    )

                    user = UserRepository.create(
                        db=db,
                        email=email,
                        provider_id=provider_id,
                        provider_user_id=provider_user_id,
                        display_name=display_name,
                        photo_url=photo_url,
                        email_verified=email_verified
                    )
                    db.commit()
                    db.refresh(user)
                    logger.info(f"[Auth] Firebase 사용자 생성 완료: user_id={user.id}, email={user.email}")
            else:
                logger.warning(
                    f"[Auth] 사용자를 찾을 수 없음: "
                    f"provider={provider_id}, provider_user_id={provider_user_id}"
                )
                raise credentials_exception

        logger.info(f"[Auth] 사용자 인증 성공: user_id={user.id}, email={user.email}")

        return user

    except HTTPException:
        raise

    except AuthInvalidTokenError as e:
        logger.warning(f"[Auth] 유효하지 않은 토큰: {e}")
        raise credentials_exception

    except Exception as e:
        logger.error(f"[Auth] 사용자 인증 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 처리 중 오류가 발생했습니다"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 활성화된 사용자만 허용

    Args:
        current_user: 현재 로그인한 사용자

    Returns:
        User: 활성화된 사용자 객체

    Raises:
        HTTPException 403: 비활성화된 사용자
    """
    if not current_user.is_active:
        logger.warning(f"[Auth] 비활성화된 사용자 접근 시도: user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    현재 관리자 사용자만 허용

    Args:
        current_user: 현재 활성화된 사용자

    Returns:
        User: 관리자 사용자 객체

    Raises:
        HTTPException 403: 관리자가 아닌 사용자
    """
    if not current_user.is_superuser:
        logger.warning(f"[Auth] 관리자 권한 없음: user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )

    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Optional[Session] = Depends(get_db_optional)
) -> Optional[User]:
    """
    선택적으로 현재 사용자 조회 (토큰이 없어도 됨)

    인증이 선택적인 엔드포인트에서 사용합니다.
    토큰이 제공되면 검증하고, 없으면 None을 반환합니다.

    Args:
        credentials: HTTP Bearer 토큰 (optional)
        db: 데이터베이스 세션

    Returns:
        Optional[User]: 인증된 사용자 객체 또는 None
    """
    if credentials is None:
        return None

    try:
        # 토큰이 있으면 검증
        token = credentials.credentials

        orchestrator = get_auth_orchestrator()
        verification_result = await orchestrator.verify_token(token)

        if not verification_result.is_valid:
            return None

        if not SQL_BACKEND_ENABLED or db is None:
            return _build_firebase_user(verification_result)

        provider_id = verification_result.provider
        provider_user_id = verification_result.user_id

        user = UserRepository.get_by_provider(
            db=db,
            provider_id=provider_id,
            provider_user_id=provider_user_id
        )

        return user

    except Exception as e:
        logger.warning(f"[Auth] 선택적 인증 실패 (무시): {e}")
        return None
