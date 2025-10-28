"""
Unit tests for AI Cache System (TASK-020)

Tests verify:
- Cache key generation (SHA-256 hashing)
- Cache hit/miss scenarios
- TTL configuration
- Cache metrics tracking
- Cache invalidation
- CachedAIOrchestrator integration
- Error handling
"""
import pytest
import time
import hashlib
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.ai.cache import AICache, AICacheMetrics
from src.ai.orchestrator import CachedAIOrchestrator
from src.ai.provider import AIProvider
from src.ai import AIResponse, GenerationConfig


class MockProvider(AIProvider):
    """Mock provider for testing"""

    def __init__(self, name: str = "mock"):
        self.api_key = "test-key"
        self.default_model = "test-model"
        self.timeout = 30
        self.max_retries = 3
        self._name = name
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def available_models(self):
        return ["test-model"]

    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Mock generation"""
        self.call_count += 1
        return AIResponse(
            content=f"Response to: {prompt}",
            model="test-model",
            provider=self._name,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str = None) -> float:
        return 0.001

    def count_tokens(self, text: str, model: str = None) -> int:
        return len(text.split())

    async def close(self):
        pass


class TestAICacheMetrics:
    """Test suite for cache metrics tracking"""

    def test_metrics_initialization(self):
        """Test metrics start at zero"""
        metrics = AICacheMetrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.errors == 0
        assert metrics.total_requests == 0
        assert metrics.get_hit_rate() == 0.0

    def test_record_hit(self):
        """Test recording cache hits"""
        metrics = AICacheMetrics()

        metrics.record_hit()
        metrics.record_hit()

        assert metrics.hits == 2
        assert metrics.total_requests == 2
        assert metrics.get_hit_rate() == 100.0

    def test_record_miss(self):
        """Test recording cache misses"""
        metrics = AICacheMetrics()

        metrics.record_miss()
        metrics.record_miss()

        assert metrics.misses == 2
        assert metrics.total_requests == 2
        assert metrics.get_hit_rate() == 0.0

    def test_mixed_hits_and_misses(self):
        """Test hit rate calculation with mixed results"""
        metrics = AICacheMetrics()

        metrics.record_hit()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()

        assert metrics.hits == 3
        assert metrics.misses == 1
        assert metrics.total_requests == 4
        assert metrics.get_hit_rate() == 75.0

    def test_record_error(self):
        """Test recording cache errors"""
        metrics = AICacheMetrics()

        metrics.record_error()

        assert metrics.errors == 1

    def test_get_stats(self):
        """Test getting comprehensive stats"""
        metrics = AICacheMetrics()

        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()
        metrics.record_error()

        stats = metrics.get_stats()

        assert stats["total_requests"] == 3
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["errors"] == 1
        assert stats["hit_rate"] == 66.67

    def test_reset_metrics(self):
        """Test resetting metrics"""
        metrics = AICacheMetrics()

        metrics.record_hit()
        metrics.record_miss()
        metrics.record_error()

        metrics.reset()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.errors == 0
        assert metrics.total_requests == 0


class TestAICacheKeyGeneration:
    """Test suite for cache key generation"""

    def test_cache_key_deterministic(self):
        """Test that same inputs generate same cache key"""
        # Create mock Redis client
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis)

        key1 = cache._generate_cache_key(
            prompt="Test prompt",
            system_prompt="System",
            model="gpt-4"
        )

        key2 = cache._generate_cache_key(
            prompt="Test prompt",
            system_prompt="System",
            model="gpt-4"
        )

        assert key1 == key2

    def test_cache_key_different_prompts(self):
        """Test that different prompts generate different keys"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis)

        key1 = cache._generate_cache_key(prompt="Prompt 1")
        key2 = cache._generate_cache_key(prompt="Prompt 2")

        assert key1 != key2

    def test_cache_key_includes_system_prompt(self):
        """Test that system prompt affects cache key"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis)

        key1 = cache._generate_cache_key(
            prompt="Test",
            system_prompt="System 1"
        )
        key2 = cache._generate_cache_key(
            prompt="Test",
            system_prompt="System 2"
        )

        assert key1 != key2

    def test_cache_key_includes_model(self):
        """Test that model affects cache key"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis)

        key1 = cache._generate_cache_key(prompt="Test", model="gpt-4")
        key2 = cache._generate_cache_key(prompt="Test", model="gpt-3.5")

        assert key1 != key2

    def test_cache_key_prefix(self):
        """Test that cache keys have correct prefix"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis, key_prefix="test_cache:")

        key = cache._generate_cache_key(prompt="Test")

        assert key.startswith("test_cache:")

    def test_cache_key_sha256_format(self):
        """Test that cache key uses SHA-256 hash"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis, key_prefix="ai_cache:")

        key = cache._generate_cache_key(prompt="Test", model="gpt-4")

        # Remove prefix
        hash_part = key.replace("ai_cache:", "")

        # SHA-256 produces 64 character hex string
        assert len(hash_part) == 64
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_cache_key_excludes_nondeterministic_params(self):
        """Test that non-deterministic params don't affect cache key"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis)

        key1 = cache._generate_cache_key(
            prompt="Test",
            timeout=30,
            max_retries=3,
            latency_ms=100
        )

        key2 = cache._generate_cache_key(
            prompt="Test",
            timeout=60,
            max_retries=5,
            latency_ms=200
        )

        # Should be the same because excluded params are ignored
        assert key1 == key2


class TestAICacheOperations:
    """Test suite for cache get/set operations"""

    def test_cache_miss(self):
        """Test cache miss scenario"""
        mock_redis = Mock()
        mock_redis.get.return_value = None

        cache = AICache(redis_client=mock_redis)

        result = cache.get(prompt="Test prompt")

        assert result is None
        assert cache.metrics.misses == 1
        assert cache.metrics.hits == 0

    def test_cache_hit(self):
        """Test cache hit scenario (TASK-020 requirement)"""
        mock_redis = Mock()

        # Mock cached response
        cached_response = AIResponse(
            content="Cached response",
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )

        cached_data = cached_response.model_dump()
        if 'created_at' in cached_data:
            cached_data['created_at'] = cached_data['created_at'].isoformat()

        mock_redis.get.return_value = json.dumps(cached_data)

        cache = AICache(redis_client=mock_redis)

        result = cache.get(prompt="Test prompt")

        assert result is not None
        assert result.content == "Cached response"
        assert result.provider == "openai"
        assert cache.metrics.hits == 1
        assert cache.metrics.misses == 0

    def test_cache_set(self):
        """Test caching a response"""
        mock_redis = Mock()

        cache = AICache(redis_client=mock_redis, default_ttl=3600)

        response = AIResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )

        result = cache.set(
            response=response,
            prompt="Test prompt",
            system_prompt="System",
            model="gpt-4"
        )

        assert result is True
        mock_redis.setex.assert_called_once()

        # Check TTL was set
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600  # TTL argument

    def test_cache_set_custom_ttl(self):
        """Test caching with custom TTL"""
        mock_redis = Mock()

        cache = AICache(redis_client=mock_redis, default_ttl=3600)

        response = AIResponse(
            content="Test",
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )

        cache.set(response=response, prompt="Test", ttl=7200)

        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 7200  # Custom TTL

    def test_cache_invalidate(self):
        """Test cache invalidation"""
        mock_redis = Mock()
        mock_redis.delete.return_value = 1

        cache = AICache(redis_client=mock_redis)

        result = cache.invalidate(prompt="Test prompt", model="gpt-4")

        assert result is True
        mock_redis.delete.assert_called_once()

    def test_cache_invalidate_nonexistent(self):
        """Test invalidating non-existent cache entry"""
        mock_redis = Mock()
        mock_redis.delete.return_value = 0

        cache = AICache(redis_client=mock_redis)

        result = cache.invalidate(prompt="Nonexistent")

        assert result is False

    def test_cache_clear_all(self):
        """Test clearing all cached entries"""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = [
            "ai_cache:key1",
            "ai_cache:key2",
            "ai_cache:key3"
        ]
        mock_redis.delete.return_value = 3

        cache = AICache(redis_client=mock_redis)

        deleted_count = cache.clear_all()

        assert deleted_count == 3
        mock_redis.delete.assert_called_once_with(
            "ai_cache:key1",
            "ai_cache:key2",
            "ai_cache:key3"
        )

    def test_cache_clear_all_empty(self):
        """Test clearing cache when no entries exist"""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = []

        cache = AICache(redis_client=mock_redis)

        deleted_count = cache.clear_all()

        assert deleted_count == 0


class TestAICacheHealthCheck:
    """Test suite for cache health checks"""

    def test_health_check_healthy(self):
        """Test health check when Redis is healthy"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "1.5M",
            "uptime_in_seconds": 3600
        }

        cache = AICache(redis_client=mock_redis)

        health = cache.health_check()

        assert health["status"] == "healthy"
        assert "response_time_ms" in health
        assert health["connected_clients"] == 5
        assert health["used_memory_human"] == "1.5M"
        assert health["uptime_seconds"] == 3600

    def test_health_check_unhealthy(self):
        """Test health check when Redis is down"""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection refused")

        cache = AICache(redis_client=mock_redis)

        health = cache.health_check()

        assert health["status"] == "unhealthy"
        assert "error" in health

    def test_health_check_no_redis(self):
        """Test health check when Redis client not initialized"""
        # Mock Redis connection failure to force redis=None
        with patch('redis.from_url', side_effect=Exception("Connection refused")):
            cache = AICache(redis_client=None)

            health = cache.health_check()

            assert health["status"] == "unhealthy"
            assert health["error"] == "Redis client not initialized"


class TestAICacheMetricsIntegration:
    """Test suite for cache metrics integration"""

    def test_get_metrics(self):
        """Test getting cache metrics"""
        mock_redis = Mock()
        mock_redis.info.return_value = {
            "keyspace_hits": 100,
            "keyspace_misses": 50
        }

        cache = AICache(redis_client=mock_redis)

        cache.metrics.record_hit()
        cache.metrics.record_miss()

        metrics = cache.get_metrics()

        assert metrics["total_requests"] == 2
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["redis_hits"] == 100
        assert metrics["redis_misses"] == 50

    def test_reset_metrics(self):
        """Test resetting cache metrics"""
        mock_redis = Mock()
        cache = AICache(redis_client=mock_redis)

        cache.metrics.record_hit()
        cache.metrics.record_miss()

        cache.reset_metrics()

        assert cache.metrics.hits == 0
        assert cache.metrics.misses == 0


class TestCachedAIOrchestratorIntegration:
    """Test suite for CachedAIOrchestrator"""

    @pytest.mark.asyncio
    async def test_cached_orchestrator_cache_miss(self):
        """Test orchestrator with cache miss - generates new response"""
        mock_redis = Mock()
        mock_redis.get.return_value = None  # Cache miss

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache,
            enable_caching=True
        )

        response = await orchestrator.generate(prompt="Test prompt")

        assert response.content == "Response to: Test prompt"
        assert response.provider == "test-provider"
        assert provider.call_count == 1  # Provider was called
        assert cache.metrics.misses == 1

        # Check that response was cached
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_orchestrator_cache_hit(self):
        """Test orchestrator with cache hit - returns cached response (TASK-020)"""
        mock_redis = Mock()

        # Mock cached response
        cached_response = AIResponse(
            content="Cached response",
            model="test-model",
            provider="test-provider",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )

        cached_data = cached_response.model_dump()
        if 'created_at' in cached_data:
            cached_data['created_at'] = cached_data['created_at'].isoformat()

        mock_redis.get.return_value = json.dumps(cached_data)

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache,
            enable_caching=True
        )

        response = await orchestrator.generate(prompt="Test prompt")

        assert response.content == "Cached response"
        assert provider.call_count == 0  # Provider was NOT called
        assert cache.metrics.hits == 1

    @pytest.mark.asyncio
    async def test_cached_orchestrator_cache_disabled(self):
        """Test orchestrator with caching disabled"""
        mock_redis = Mock()

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache,
            enable_caching=False
        )

        response = await orchestrator.generate(prompt="Test prompt")

        assert provider.call_count == 1  # Provider was called
        mock_redis.get.assert_not_called()  # Cache not checked

    @pytest.mark.asyncio
    async def test_cached_orchestrator_use_cache_false(self):
        """Test orchestrator with use_cache=False parameter"""
        mock_redis = Mock()

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache,
            enable_caching=True
        )

        response = await orchestrator.generate(
            prompt="Test prompt",
            use_cache=False
        )

        assert provider.call_count == 1
        mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_orchestrator_get_cache_metrics(self):
        """Test getting cache metrics from orchestrator"""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.info.return_value = {}

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache
        )

        await orchestrator.generate(prompt="Test 1")
        await orchestrator.generate(prompt="Test 2")

        metrics = orchestrator.get_cache_metrics()

        assert metrics["total_requests"] == 2
        assert metrics["misses"] == 2

    @pytest.mark.asyncio
    async def test_cached_orchestrator_invalidate_cache(self):
        """Test cache invalidation through orchestrator"""
        mock_redis = Mock()
        mock_redis.delete.return_value = 1

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache
        )

        result = orchestrator.invalidate_cache(
            prompt="Test prompt",
            model="gpt-4"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_cached_orchestrator_clear_all_cache(self):
        """Test clearing all cache through orchestrator"""
        mock_redis = Mock()
        mock_redis.scan_iter.return_value = ["key1", "key2"]
        mock_redis.delete.return_value = 2

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache
        )

        deleted = orchestrator.clear_all_cache()

        assert deleted == 2

    @pytest.mark.asyncio
    async def test_cached_orchestrator_get_cache_health(self):
        """Test getting cache health through orchestrator"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "connected_clients": 1,
            "used_memory_human": "100K",
            "uptime_in_seconds": 600
        }

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache
        )

        health = orchestrator.get_cache_health()

        assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_cached_orchestrator_close_all(self):
        """Test closing all connections including cache"""
        mock_redis = Mock()

        cache = AICache(redis_client=mock_redis)
        provider = MockProvider("test-provider")

        orchestrator = CachedAIOrchestrator(
            providers=[provider],
            cache=cache
        )

        await orchestrator.close_all()

        mock_redis.close.assert_called_once()


class TestCacheErrorHandling:
    """Test suite for cache error handling"""

    def test_cache_get_error_handling(self):
        """Test that cache errors are handled gracefully on get"""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis error")

        cache = AICache(redis_client=mock_redis)

        result = cache.get(prompt="Test")

        assert result is None
        assert cache.metrics.errors == 1

    def test_cache_set_error_handling(self):
        """Test that cache errors are handled gracefully on set"""
        mock_redis = Mock()
        mock_redis.setex.side_effect = Exception("Redis error")

        cache = AICache(redis_client=mock_redis)

        response = AIResponse(
            content="Test",
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001
        )

        result = cache.set(response=response, prompt="Test")

        assert result is False
        assert cache.metrics.errors == 1

    def test_cache_operations_with_no_redis(self):
        """Test cache operations when Redis client is None"""
        # Mock Redis connection failure to force redis=None
        with patch('redis.from_url', side_effect=Exception("Connection refused")):
            cache = AICache(redis_client=None)

            # Get should return None
            assert cache.get(prompt="Test") is None

            # Set should return False
            response = AIResponse(
                content="Test",
                model="gpt-4",
                provider="openai",
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                estimated_cost=0.001
            )
            assert cache.set(response=response, prompt="Test") is False

            # Invalidate should return False
            assert cache.invalidate(prompt="Test") is False

            # Clear all should return 0
            assert cache.clear_all() == 0
