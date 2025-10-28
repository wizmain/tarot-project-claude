"""
Firebase Admin SDK 초기화 모듈

Firebase Admin SDK를 초기화하고 관리하는 모듈입니다.
"""
import firebase_admin
from firebase_admin import credentials
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)


def initialize_firebase_admin():
    """
    Firebase Admin SDK 초기화

    환경 변수에서 Firebase 설정을 읽어 Admin SDK를 초기화합니다.
    이미 초기화된 경우 다시 초기화하지 않습니다.

    설정:
    - FIREBASE_CREDENTIALS_PATH: Service Account Key JSON 파일 경로
    """
    # 이미 초기화되었는지 확인
    if firebase_admin._apps:
        logger.info("Firebase Admin SDK already initialized")
        return

    try:
        # Firebase credentials path 확인
        credentials_path = settings.FIREBASE_CREDENTIALS_PATH

        if not credentials_path:
            logger.warning(
                "Firebase credentials path not configured. "
                "Firebase features will not be available."
            )
            return

        # Certificate 로드
        cred = credentials.Certificate(credentials_path)

        # Firebase Admin 초기화
        firebase_admin.initialize_app(cred)

        logger.info("Firebase Admin SDK initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise


def is_firebase_enabled() -> bool:
    """
    Firebase가 활성화되어 있는지 확인

    Returns:
        True if Firebase is initialized, False otherwise
    """
    return len(firebase_admin._apps) > 0
