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
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.config import settings
from src.core.logging import get_logger
from src.auth import AuthOrchestrator, AuthProviderFactory
from src.auth.models import AuthProviderError, AuthInvalidTokenError
from src.api.repositories.user_repository import UserRepository
from src.models import User

logger = get_logger(__name__)

# HTTP Bearer 토큰 스키마 (Authorization: Bearer <token>)
security = HTTPBearer()

# Auth Orchestrator 싱글톤
_auth_orchestrator = None


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
        primary_provider = getattr(settings, 'AUTH_PRIMARY_PROVIDER', 'custom_jwt')

        # Provider 설정
        configs = {}

        # Custom JWT Provider 설정
        configs['custom_jwt'] = {
            'secret_key': settings.SECRET_KEY,
            'algorithm': 'HS256',
            'access_token_expire_minutes': 60,
            'refresh_token_expire_days': 7,
        }

        # Firebase Provider 설정 (선택적)
        if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH'):
            configs['firebase'] = {
                'credentials_path': settings.FIREBASE_CREDENTIALS_PATH
            }

        # Auth0 Provider 설정 (선택적)
        if hasattr(settings, 'AUTH0_DOMAIN') and hasattr(settings, 'AUTH0_CLIENT_ID'):
            configs['auth0'] = {
                'domain': settings.AUTH0_DOMAIN,
                'client_id': settings.AUTH0_CLIENT_ID,
                'client_secret': getattr(settings, 'AUTH0_CLIENT_SECRET', None),
            }

        # Fallback providers
        fallback_providers = []
        if 'firebase' in configs and primary_provider != 'firebase':
            fallback_providers.append('firebase')
        if 'auth0' in configs and primary_provider != 'auth0':
            fallback_providers.append('auth0')

        try:
            _auth_orchestrator = AuthOrchestrator(
                primary_provider=primary_provider,
                fallback_providers=fallback_providers if fallback_providers else None,
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
    db: Session = Depends(get_db)
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
        provider_id = verification_result.provider if hasattr(verification_result, 'provider') else orchestrator.primary_provider_name

        # Provider에 따라 provider_user_id 형식 결정
        if provider_id == 'firebase':
            # Firebase는 user_id를 그대로 사용
            provider_user_id = verification_result.user_id
        else:
            # Custom JWT는 jwt_ 접두사 사용
            provider_user_id = f"jwt_{verification_result.user_id}"

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
    db: Session = Depends(get_db)
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

        # Provider User ID로 사용자 조회
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
