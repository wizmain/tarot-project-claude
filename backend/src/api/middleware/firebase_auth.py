"""
Firebase Authentication Middleware

Firebase ID 토큰을 검증하는 미들웨어입니다.
"""
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from src.core.firebase_admin import is_firebase_enabled
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Firebase ID 토큰 검증

    Authorization 헤더의 Bearer 토큰을 검증합니다.
    검증에 성공하면 사용자 ID(uid)를 반환합니다.

    Args:
        credentials: HTTPBearer로 추출된 인증 정보

    Returns:
        str: Firebase User ID (uid)

    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    if not is_firebase_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not configured"
        )

    try:
        # Firebase ID 토큰 검증
        decoded_token = auth.verify_id_token(credentials.credentials)
        user_id = decoded_token['uid']

        logger.debug(f"Firebase token verified for user: {user_id}")
        return user_id

    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )

    except auth.RevokedIdTokenError:
        logger.warning("Firebase token revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked"
        )

    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)
) -> Optional[str]:
    """
    선택적 Firebase 인증

    토큰이 있으면 검증하고, 없으면 None을 반환합니다.
    인증이 필수가 아닌 엔드포인트에서 사용합니다.

    Args:
        credentials: HTTPBearer로 추출된 인증 정보 (optional)

    Returns:
        Optional[str]: Firebase User ID (uid) 또는 None
    """
    if not credentials:
        return None

    try:
        return await verify_firebase_token(credentials)
    except HTTPException:
        return None
