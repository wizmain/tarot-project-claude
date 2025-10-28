"""
Redis 캐시 설정 및 유틸리티 모듈

이 모듈의 목적:
- Redis 기반 캐싱 시스템 제공
- AI 응답, API 결과 등 자주 사용되는 데이터 캐싱
- 데코레이터를 통한 간편한 캐시 적용
- 해시 기반 캐시 키 생성으로 일관성 보장

주요 기능:
- get/set/delete: 기본 캐시 CRUD 작업
- cached 데코레이터: 함수 결과 자동 캐싱
- hash_key: 함수 인자를 해시하여 캐시 키 생성
"""
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import redis
from src.core.config import settings


class RedisCache:
    """
    Redis 캐시 관리자

    Redis 서버와 연결하여 데이터를 캐싱하고 조회합니다.
    JSON 직렬화를 통해 다양한 Python 객체를 캐시할 수 있습니다.
    """

    def __init__(self):
        """Redis 연결 초기화"""
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = json.dumps(value)
            if ttl:
                self.redis_client.setex(key, ttl, serialized_value)
            else:
                self.redis_client.set(key, serialized_value)
            return True
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Redis EXISTS error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis CLEAR PATTERN error: {e}")
            return 0

    def ping(self) -> bool:
        """
        Test Redis connection

        Returns:
            True if connection is alive, False otherwise
        """
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Redis PING error: {e}")
            return False


# Global cache instance
cache = RedisCache()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results

    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache key

    Usage:
        @cached(ttl=300, key_prefix="user")
        def get_user(user_id: int):
            return fetch_user_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]

            # Add args to key
            if args:
                args_str = json.dumps(args, sort_keys=True, default=str)
                key_parts.append(hashlib.md5(args_str.encode()).hexdigest()[:8])

            # Add kwargs to key
            if kwargs:
                kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
                key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])

            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
