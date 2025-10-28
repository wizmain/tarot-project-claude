"""
AI Response Caching System

Implements TASK-020: Redis-based caching for AI responses
"""
import hashlib
import json
import time
from typing import Optional, Dict, Any
import logging
from datetime import datetime

import redis
from redis import Redis

from src.ai.models import AIResponse

logger = logging.getLogger(__name__)


class AICacheMetrics:
    """Tracks cache hit/miss metrics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_requests = 0

    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1
        self.total_requests += 1

    def record_miss(self):
        """Record a cache miss"""
        self.misses += 1
        self.total_requests += 1

    def record_error(self):
        """Record a cache error"""
        self.errors += 1

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_requests": self.total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": round(self.get_hit_rate(), 2),
        }

    def reset(self):
        """Reset all metrics"""
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_requests = 0


class AICache:
    """
    Redis-based cache for AI responses

    Features:
    - Prompt-based cache keys using SHA-256 hashing
    - TTL support (default 24 hours)
    - Cache hit/miss metrics
    - Automatic serialization/deserialization
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 86400,  # 24 hours in seconds
        key_prefix: str = "ai_cache:"
    ):
        """
        Initialize AI cache

        Args:
            redis_client: Redis client instance (optional)
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds (24 hours)
            key_prefix: Prefix for cache keys
        """
        if redis_client:
            self.redis = redis_client
        else:
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis.ping()
                logger.info(f"[AICache] Connected to Redis: {redis_url}")
            except Exception as e:
                logger.error(f"[AICache] Failed to connect to Redis: {e}")
                self.redis = None

        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.metrics = AICacheMetrics()

    def _generate_cache_key(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate cache key from prompt and parameters

        Uses SHA-256 hashing for consistent key generation

        Args:
            prompt: User prompt
            system_prompt: System instruction
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Cache key string
        """
        # Build cache key components
        key_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": model,
        }

        # Add relevant kwargs (exclude non-deterministic values)
        excluded_keys = {"timeout", "max_retries", "latency_ms", "created_at"}
        for key, value in kwargs.items():
            if key not in excluded_keys and value is not None:
                key_data[key] = value

        # Create deterministic JSON string
        key_string = json.dumps(key_data, sort_keys=True)

        # Generate SHA-256 hash
        hash_object = hashlib.sha256(key_string.encode())
        hash_hex = hash_object.hexdigest()

        return f"{self.key_prefix}{hash_hex}"

    def get(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Optional[AIResponse]:
        """
        Get cached AI response

        Args:
            prompt: User prompt
            system_prompt: System instruction
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Cached AIResponse or None if not found
        """
        if not self.redis:
            return None

        try:
            cache_key = self._generate_cache_key(prompt, system_prompt, model, **kwargs)

            # Get from Redis
            cached_data = self.redis.get(cache_key)

            if cached_data:
                # Cache hit
                self.metrics.record_hit()

                # Deserialize
                data = json.loads(cached_data)
                response = AIResponse(**data)

                logger.info(
                    f"[AICache] ✓ Cache HIT: {cache_key[:16]}... "
                    f"(provider={response.provider}, model={response.model})"
                )

                return response
            else:
                # Cache miss
                self.metrics.record_miss()
                logger.debug(f"[AICache] ✗ Cache MISS: {cache_key[:16]}...")
                return None

        except Exception as e:
            self.metrics.record_error()
            logger.error(f"[AICache] Error getting from cache: {e}")
            return None

    def set(
        self,
        response: AIResponse,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """
        Cache AI response

        Args:
            response: AIResponse to cache
            prompt: User prompt
            system_prompt: System instruction
            model: Model name
            ttl: Time to live in seconds (uses default if None)
            **kwargs: Additional parameters

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.redis:
            return False

        try:
            cache_key = self._generate_cache_key(prompt, system_prompt, model, **kwargs)

            # Serialize response
            data = response.model_dump() if hasattr(response, 'model_dump') else response.dict()

            # Convert datetime to ISO format
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()

            cache_data = json.dumps(data)

            # Set with TTL
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            self.redis.setex(cache_key, ttl_seconds, cache_data)

            logger.info(
                f"[AICache] Cached response: {cache_key[:16]}... "
                f"(TTL={ttl_seconds}s, provider={response.provider})"
            )

            return True

        except Exception as e:
            self.metrics.record_error()
            logger.error(f"[AICache] Error caching response: {e}")
            return False

    def invalidate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Invalidate (delete) cached response

        Args:
            prompt: User prompt
            system_prompt: System instruction
            model: Model name
            **kwargs: Additional parameters

        Returns:
            True if deleted, False otherwise
        """
        if not self.redis:
            return False

        try:
            cache_key = self._generate_cache_key(prompt, system_prompt, model, **kwargs)
            deleted = self.redis.delete(cache_key)

            if deleted:
                logger.info(f"[AICache] Invalidated cache: {cache_key[:16]}...")
                return True
            else:
                logger.debug(f"[AICache] No cache to invalidate: {cache_key[:16]}...")
                return False

        except Exception as e:
            logger.error(f"[AICache] Error invalidating cache: {e}")
            return False

    def clear_all(self) -> int:
        """
        Clear all cached responses with the key prefix

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            return 0

        try:
            pattern = f"{self.key_prefix}*"
            keys = list(self.redis.scan_iter(match=pattern))

            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"[AICache] Cleared {deleted} cached responses")
                return deleted
            else:
                logger.debug("[AICache] No cached responses to clear")
                return 0

        except Exception as e:
            logger.error(f"[AICache] Error clearing cache: {e}")
            return 0

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache metrics

        Returns:
            Dictionary with cache statistics
        """
        stats = self.metrics.get_stats()

        # Add Redis info if available
        if self.redis:
            try:
                info = self.redis.info("stats")
                stats["redis_hits"] = info.get("keyspace_hits", 0)
                stats["redis_misses"] = info.get("keyspace_misses", 0)
            except Exception as e:
                logger.warning(f"[AICache] Could not get Redis stats: {e}")

        return stats

    def reset_metrics(self):
        """Reset cache metrics"""
        self.metrics.reset()
        logger.info("[AICache] Metrics reset")

    def health_check(self) -> Dict[str, Any]:
        """
        Check cache health

        Returns:
            Health status dictionary
        """
        if not self.redis:
            return {
                "status": "unhealthy",
                "error": "Redis client not initialized"
            }

        try:
            # Test ping
            response_time_start = time.time()
            self.redis.ping()
            response_time = (time.time() - response_time_start) * 1000

            # Get info
            info = self.redis.info()

            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def close(self):
        """Close Redis connection"""
        if self.redis:
            try:
                self.redis.close()
                logger.info("[AICache] Redis connection closed")
            except Exception as e:
                logger.warning(f"[AICache] Error closing Redis connection: {e}")
