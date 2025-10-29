"""
Firebase Admin SDK 초기화 모듈

Firebase Admin SDK를 초기화하고 관리하는 모듈입니다.
"""
import firebase_admin
from firebase_admin import credentials
from src.core.config import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def initialize_firebase_admin():
    """
    Firebase Admin SDK 초기화

    환경 변수에서 Firebase 설정을 읽어 Admin SDK를 초기화합니다.
    이미 초기화된 경우 다시 초기화하지 않습니다.

    설정:
    - FIREBASE_CREDENTIALS_PATH: Service Account Key JSON 파일 경로
    - Cloud Run 환경에서는 Application Default Credentials (ADC) 사용
    """
    # 이미 초기화되었는지 확인
    if firebase_admin._apps:
        logger.info("Firebase Admin SDK already initialized")
        return

    try:
        # Firebase credentials path 확인
        credentials_path = settings.FIREBASE_CREDENTIALS_PATH

        if credentials_path:
            path_obj = Path(credentials_path)
            if path_obj.is_file():
                # 로컬 환경: JSON 파일 사용
                logger.info("Initializing Firebase with credentials file: %s", credentials_path)
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
            else:
                logger.warning(
                    "Firebase credentials file not found at %s. Falling back to Application Default Credentials.",
                    credentials_path,
                )
                firebase_admin.initialize_app()
        else:
            # Cloud Run 환경: Application Default Credentials 사용
            logger.info("Initializing Firebase with Application Default Credentials")
            firebase_admin.initialize_app()

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
