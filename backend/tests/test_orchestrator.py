"""
Unit tests for AI Orchestrator (TASK-019)

Tests verify:
- Primary provider success
- Primary failure with fallback success
- All providers failure
- Timeout handling (3-second requirement)
- Retry logic with exponential backoff
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from typing import List

from src.ai.orchestrator import AIOrchestrator
from src.ai.provider import AIProvider
from src.ai import (
    AIResponse,
    GenerationConfig,
    AIProviderError,
    AIRateLimitError,
    AIAuthenticationError,
    AITimeoutError,
)


class MockProvider(AIProvider):
    """Mock provider for testing"""

    def __init__(self, name: str, should_succeed: bool = True, delay: float = 0):
        self.api_key = "test-key"
        self.default_model = "test-model"
        self.timeout = 30
        self.max_retries = 3
        self._name = name
        self.should_succeed = should_succeed
        self.delay = delay
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def available_models(self) -> List[str]:
        return ["test-model"]

    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Mock generation with configurable behavior"""
        self.call_count += 1

        # Simulate delay if specified
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        if not self.should_succeed:
            raise AIProviderError(
                f"Provider {self._name} failed",
                provider=self._name,
                error_type="TEST_FAILURE"
            )

        return AIResponse(
            content=f"Response from {self._name}",
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


class TestOrchestratorInitialization:
    """Test suite for orchestrator initialization"""

    def test_orchestrator_single_provider(self):
        """Test orchestrator with single provider"""
        provider = MockProvider("primary")
        orchestrator = AIOrchestrator([provider])

        assert orchestrator.primary_provider == provider
        assert len(orchestrator.fallback_providers) == 0
        assert orchestrator.provider_timeout == 3
        assert orchestrator.max_retries == 2

    def test_orchestrator_multiple_providers(self):
        """Test orchestrator with multiple providers"""
        primary = MockProvider("primary")
        fallback1 = MockProvider("fallback1")
        fallback2 = MockProvider("fallback2")

        orchestrator = AIOrchestrator([primary, fallback1, fallback2])

        assert orchestrator.primary_provider == primary
        assert len(orchestrator.fallback_providers) == 2
        assert orchestrator.fallback_providers[0] == fallback1
        assert orchestrator.fallback_providers[1] == fallback2

    def test_orchestrator_empty_providers_raises_error(self):
        """Test that empty provider list raises error"""
        with pytest.raises(ValueError, match="At least one provider must be specified"):
            AIOrchestrator([])

    def test_orchestrator_custom_timeout(self):
        """Test orchestrator with custom timeout"""
        provider = MockProvider("primary")
        orchestrator = AIOrchestrator([provider], provider_timeout=5, max_retries=3)

        assert orchestrator.provider_timeout == 5
        assert orchestrator.max_retries == 3


class TestOrchestratorPrimarySuccess:
    """Test suite for primary provider success scenarios"""

    @pytest.mark.asyncio
    async def test_primary_provider_succeeds(self):
        """Test that primary provider is used when it succeeds"""
        primary = MockProvider("primary", should_succeed=True)
        fallback = MockProvider("fallback", should_succeed=True)

        orchestrator = AIOrchestrator([primary, fallback])

        response = await orchestrator.generate(prompt="Test prompt")

        assert response.content == "Response from primary"
        assert response.provider == "primary"
        assert primary.call_count == 1
        assert fallback.call_count == 0  # Fallback should not be called

    @pytest.mark.asyncio
    async def test_primary_provider_fast_response(self):
        """Test that primary provider responds quickly"""
        primary = MockProvider("primary", should_succeed=True, delay=0.1)

        orchestrator = AIOrchestrator([primary])

        start_time = time.time()
        response = await orchestrator.generate(prompt="Test prompt")
        elapsed = time.time() - start_time

        assert response.provider == "primary"
        assert elapsed < 1.0  # Should be fast


class TestOrchestratorFallback:
    """Test suite for fallback scenarios"""

    @pytest.mark.asyncio
    async def test_primary_fails_fallback_succeeds(self):
        """Test fallback when primary provider fails"""
        primary = MockProvider("primary", should_succeed=False)
        fallback = MockProvider("fallback", should_succeed=True)

        orchestrator = AIOrchestrator([primary, fallback])

        response = await orchestrator.generate(prompt="Test prompt")

        assert response.content == "Response from fallback"
        assert response.provider == "fallback"
        assert primary.call_count > 0  # Primary was attempted
        assert fallback.call_count == 1  # Fallback was used

    @pytest.mark.asyncio
    async def test_multiple_fallbacks(self):
        """Test that multiple fallbacks are tried in order"""
        primary = MockProvider("primary", should_succeed=False)
        fallback1 = MockProvider("fallback1", should_succeed=False)
        fallback2 = MockProvider("fallback2", should_succeed=True)

        orchestrator = AIOrchestrator([primary, fallback1, fallback2])

        response = await orchestrator.generate(prompt="Test prompt")

        assert response.provider == "fallback2"
        assert primary.call_count > 0
        assert fallback1.call_count > 0
        assert fallback2.call_count == 1

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test that error is raised when all providers fail"""
        primary = MockProvider("primary", should_succeed=False)
        fallback = MockProvider("fallback", should_succeed=False)

        orchestrator = AIOrchestrator([primary, fallback])

        with pytest.raises(AIProviderError, match="All 2 providers failed"):
            await orchestrator.generate(prompt="Test prompt")

        assert primary.call_count > 0
        assert fallback.call_count > 0


class TestOrchestratorTimeout:
    """Test suite for timeout handling"""

    @pytest.mark.asyncio
    async def test_provider_timeout_triggers_fallback(self):
        """Test that timeout triggers fallback (TASK-019 requirement: 3-second timeout)"""
        # Primary takes 5 seconds (exceeds 3-second timeout)
        primary = MockProvider("primary", should_succeed=True, delay=5.0)
        fallback = MockProvider("fallback", should_succeed=True, delay=0.1)

        # Use max_retries=1 to avoid long waits
        orchestrator = AIOrchestrator([primary, fallback], provider_timeout=3, max_retries=1)

        start_time = time.time()
        response = await orchestrator.generate(prompt="Test prompt")
        elapsed = time.time() - start_time

        assert response.provider == "fallback"
        # With 1 retry: 3s timeout + quick fallback < 5s
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_timeout_within_3_seconds(self):
        """Test that timeout happens within 3 seconds per provider (TASK-019 requirement)"""
        primary = MockProvider("primary", should_succeed=True, delay=10.0)
        fallback = MockProvider("fallback", should_succeed=True, delay=0.1)

        orchestrator = AIOrchestrator([primary, fallback], provider_timeout=3, max_retries=1)

        start_time = time.time()
        response = await orchestrator.generate(prompt="Test prompt")
        elapsed = time.time() - start_time

        # Primary should timeout within 3 seconds and fallback should succeed
        assert response.provider == "fallback"
        assert elapsed < 5.0  # 3s timeout + quick fallback


class TestOrchestratorRetryLogic:
    """Test suite for retry logic"""

    @pytest.mark.asyncio
    async def test_retries_on_rate_limit(self):
        """Test that transient errors trigger retries"""
        call_count = 0

        class RetryProvider(MockProvider):
            async def generate(self, prompt: str, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 2:  # Fail first attempt
                    raise AIRateLimitError("Rate limited", provider=self._name)
                # Succeed on retry
                return await super().generate(prompt, **kwargs)

        provider = RetryProvider("primary", should_succeed=True)
        orchestrator = AIOrchestrator([provider], max_retries=3)

        response = await orchestrator.generate(prompt="Test prompt")

        assert response.provider == "primary"
        assert call_count == 2  # Initial attempt + 1 retry

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """Test that non-retryable errors don't trigger retries"""
        call_count = 0

        class AuthFailProvider(MockProvider):
            async def generate(self, prompt: str, **kwargs):
                nonlocal call_count
                call_count += 1
                raise AIAuthenticationError("Invalid API key", provider=self._name)

        primary = AuthFailProvider("primary", should_succeed=False)
        fallback = MockProvider("fallback", should_succeed=True)

        orchestrator = AIOrchestrator([primary, fallback], max_retries=3)

        response = await orchestrator.generate(prompt="Test prompt")

        # Should immediately fallback without retries
        assert response.provider == "fallback"
        assert call_count == 1  # No retries for auth error


class TestOrchestratorStatus:
    """Test suite for orchestrator status"""

    def test_get_provider_status(self):
        """Test getting orchestrator status"""
        primary = MockProvider("primary")
        fallback = MockProvider("fallback")

        orchestrator = AIOrchestrator([primary, fallback], provider_timeout=5, max_retries=3)

        status = orchestrator.get_provider_status()

        assert status["total_providers"] == 2
        assert status["primary_provider"]["name"] == "primary"
        assert len(status["fallback_providers"]) == 1
        assert status["fallback_providers"][0]["name"] == "fallback"
        assert status["timeout_seconds"] == 5
        assert status["max_retries"] == 3

    @pytest.mark.asyncio
    async def test_close_all_providers(self):
        """Test closing all provider connections"""
        primary = MockProvider("primary")
        fallback = MockProvider("fallback")

        orchestrator = AIOrchestrator([primary, fallback])

        # Should not raise error
        await orchestrator.close_all()
