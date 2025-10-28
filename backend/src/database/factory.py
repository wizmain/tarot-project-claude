"""
Database Provider Factory

환경 변수를 통해 사용할 데이터베이스 Provider를 선택합니다.
"""
from typing import Optional
from src.core.config import settings
from .provider import DatabaseProvider


_provider_instance: Optional[DatabaseProvider] = None


def get_database_provider() -> DatabaseProvider:
    """
    데이터베이스 Provider 싱글톤 인스턴스 가져오기

    환경 변수 DATABASE_PROVIDER로 Provider 선택:
    - 'postgresql' (기본값): PostgreSQL 사용
    - 'firestore': Firestore 사용
    """
    global _provider_instance

    if _provider_instance is None:
        provider_type = getattr(settings, 'DATABASE_PROVIDER', 'postgresql').lower()

        if provider_type == 'firestore':
            from .firestore_provider import FirestoreProvider
            _provider_instance = FirestoreProvider()
        else:
            # 기본값: PostgreSQL
            from .postgresql_provider import PostgreSQLProvider
            _provider_instance = PostgreSQLProvider()

    return _provider_instance


def reset_database_provider() -> None:
    """
    Provider 인스턴스 초기화 (주로 테스트용)
    """
    global _provider_instance
    _provider_instance = None
