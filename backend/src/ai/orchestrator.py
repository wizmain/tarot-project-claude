"""
AI Orchestrator - 다중 AI Provider 조율 및 Fallback 관리 모듈

이 모듈의 목적:
- 여러 AI Provider를 순차적으로 시도하여 안정성 확보
- Primary/Secondary Provider 구조로 가용성 향상
- 타임아웃 관리 및 자동 재시도 (Exponential Backoff)
- 상세한 로깅을 통한 장애 추적

주요 기능:
- 다중 Provider 자동 Fallback (3초 타임아웃)
- 재시도 로직 (최대 3회, 지수 백오프)
- 비용 추정 및 성능 메트릭 수집
- 에러 타입별 처리 전략

TASK-019: Fallback 메커니즘 구현
TASK-020: AI 응답 캐싱 시스템 (CachedAIOrchestrator)

사용 예시:
    orchestrator = AIOrchestrator(
        providers=[openai_provider, claude_provider],
        timeout=3.0
    )
    response = await orchestrator.generate(
        prompt="타로 리딩 요청",
        config=GenerationConfig(max_tokens=1000)
    )
"""
import time
import asyncio
from typing import List, Optional, Dict, Any
import logging

from src.ai.provider import AIProvider
from src.ai.models import (
    AIResponse,
    OrchestratorResponse,
    AIProviderError,
    AIRateLimitError,
    AIAuthenticationError,
    AITimeoutError,
    AIServiceUnavailableError,
    GenerationConfig,
)

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    AI Provider 오케스트레이터

    여러 AI Provider를 관리하고 장애 발생 시 자동으로 다음 Provider로
    전환하여 서비스 가용성을 보장합니다.

    주요 특징:
    - Primary Provider 실패 시 3초 이내 Secondary로 Fallback
    - 지수 백오프(Exponential Backoff)를 통한 지능적 재시도
    - 포괄적인 에러 핸들링 및 로깅
    - 요청당 최대 타임아웃 설정 가능
    """

    def __init__(
        self,
        providers: List[AIProvider],
        provider_timeout: int = 30,
        max_retries: int = 2
    ):
        """
        Initialize AI Orchestrator

        Args:
            providers: List of AI providers (first is primary)
            provider_timeout: Timeout per provider in seconds (default 30s)
            max_retries: Maximum retries per provider (default 2)
        """
        if not providers:
            raise ValueError("At least one provider must be specified")

        self.providers = providers
        self.primary_provider = providers[0]
        self.fallback_providers = providers[1:] if len(providers) > 1 else []
        self.provider_timeout = provider_timeout
        self.max_retries = max_retries

        logger.info(
            f"AIOrchestrator initialized with {len(providers)} providers: "
            f"Primary={self.primary_provider.provider_name}, "
            f"Fallbacks={[p.provider_name for p in self.fallback_providers]}"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> OrchestratorResponse:
        """
        Generate text with automatic fallback

        Tries providers in order:
        1. Primary provider (with retries)
        2. Fallback providers (if primary fails)

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            OrchestratorResponse with successful response and all attempts

        Raises:
            AIProviderError: If all providers fail
        """
        start_time = time.time()
        errors: List[Dict[str, Any]] = []
        all_attempts: List[AIResponse] = []
        
        # 모델명이 지정된 경우, 해당 모델을 지원하는 provider만 필터링
        compatible_providers = self._get_compatible_providers(model)
        
        if not compatible_providers:
            error_msg = (
                f"No compatible provider found for model '{model}'. "
                f"Available providers: {[p.provider_name for p in self.providers]}"
            )
            logger.error(f"[Orchestrator] {error_msg}")
            raise AIProviderError(
                message=error_msg,
                provider="orchestrator",
                error_type="NO_COMPATIBLE_PROVIDER",
                original_error=None
            )

        # Try compatible providers in order (maintaining priority)
        for idx, provider in enumerate(compatible_providers):
            is_primary = (provider == self.primary_provider)
            provider_label = "primary" if is_primary else f"fallback {idx}"
            
            logger.info(
                f"[Orchestrator] Attempting {provider_label} provider: {provider.provider_name}"
            )

            try:
                response = await self._try_provider(
                    provider=provider,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    config=config,
                    model=model,
                    is_primary=is_primary,
                    **kwargs
                )
                all_attempts.append(response)

                elapsed = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[Orchestrator] ✓ {provider_label.capitalize()} provider succeeded "
                    f"({provider.provider_name}) in {elapsed}ms"
                )

                total_cost = sum(attempt.estimated_cost or 0.0 for attempt in all_attempts)
                return OrchestratorResponse(
                    response=response,
                    all_attempts=all_attempts,
                    total_cost=total_cost
                )

            except Exception as e:
                error_info = {
                    "provider": provider.provider_name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "is_primary": is_primary
                }
                errors.append(error_info)

                logger.warning(
                    f"[Orchestrator] ✗ {provider_label.capitalize()} provider failed "
                    f"({provider.provider_name}): {error_info['error_type']} - {str(e)}"
                )

        # All providers failed
        total_elapsed = int((time.time() - start_time) * 1000)
        error_summary = self._format_error_summary(errors)

        logger.error(
            f"[Orchestrator] ✗ All providers failed after {total_elapsed}ms. "
            f"Errors: {error_summary}"
        )

        raise AIProviderError(
            message=f"All {len(compatible_providers)} compatible providers failed. {error_summary}",
            provider="orchestrator",
            error_type="ALL_PROVIDERS_FAILED",
            original_error=None
        )
    
    def _get_compatible_providers(self, model: Optional[str]) -> List[AIProvider]:
        """
        모델명에 따라 호환되는 provider 리스트 반환
        
        모델명이 지정된 경우, 해당 모델을 지원하는 provider만 반환합니다.
        우선순위 순서는 유지됩니다 (primary → fallback 순서).
        
        Args:
            model: 모델명 (None이면 모든 provider 반환)
        
        Returns:
            호환되는 provider 리스트 (우선순위 순서 유지)
        """
        if model is None:
            # 모델명이 없으면 모든 provider 반환
            return self.providers
        
        compatible = []
        for provider in self.providers:
            # provider가 모델을 지원하는지 확인
            if model in provider.available_models:
                compatible.append(provider)
                logger.debug(
                    f"[Orchestrator] Provider {provider.provider_name} supports model {model}"
                )
            else:
                logger.debug(
                    f"[Orchestrator] Provider {provider.provider_name} does not support model {model} "
                    f"(available models: {len(provider.available_models)} total)"
                )
        
        if compatible:
            logger.info(
                f"[Orchestrator] Found {len(compatible)} compatible provider(s) for model '{model}': "
                f"{[p.provider_name for p in compatible]}"
            )
        
        return compatible

    async def _try_provider(
        self,
        provider: AIProvider,
        prompt: str,
        system_prompt: Optional[str],
        config: Optional[GenerationConfig],
        model: Optional[str],
        is_primary: bool,
        **kwargs
    ) -> AIResponse:
        """
        Try a single provider with timeout and retries

        Args:
            provider: AI provider to use
            prompt: User prompt
            system_prompt: System instruction
            config: Generation config
            model: Model to use
            is_primary: Whether this is the primary provider
            **kwargs: Additional parameters

        Returns:
            AIResponse from provider

        Raises:
            Exception: If provider fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                # Apply timeout
                response = await asyncio.wait_for(
                    provider.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        config=config,
                        model=model,
                        **kwargs
                    ),
                    timeout=self.provider_timeout
                )

                return response

            except asyncio.TimeoutError:
                logger.warning(
                    f"[Orchestrator] Provider {provider.provider_name} timed out "
                    f"(attempt {attempt + 1}/{self.max_retries}, timeout={self.provider_timeout}s)"
                )

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    backoff = min(2 ** attempt, 4)  # Max 4 seconds
                    logger.debug(f"[Orchestrator] Waiting {backoff}s before retry...")
                    await asyncio.sleep(backoff)
                else:
                    raise AITimeoutError(
                        f"Provider {provider.provider_name} timed out after {self.max_retries} attempts",
                        provider=provider.provider_name
                    )

            except (AIRateLimitError, AIServiceUnavailableError) as e:
                # Transient errors - retry with backoff
                logger.warning(
                    f"[Orchestrator] Provider {provider.provider_name} returned transient error: {type(e).__name__}"
                )

                if attempt < self.max_retries - 1:
                    backoff = min(2 ** attempt, 4)
                    logger.debug(f"[Orchestrator] Waiting {backoff}s before retry...")
                    await asyncio.sleep(backoff)
                else:
                    raise

            except (AIAuthenticationError, AIProviderError) as e:
                # Non-retryable errors - fail immediately
                logger.error(
                    f"[Orchestrator] Provider {provider.provider_name} returned non-retryable error: "
                    f"{type(e).__name__} - {str(e)}"
                )
                raise

    def _format_error_summary(self, errors: List[Dict[str, Any]]) -> str:
        """
        Format error summary for logging

        Args:
            errors: List of error information dictionaries

        Returns:
            Formatted error summary string
        """
        if not errors:
            return "No errors recorded"

        summary_parts = []
        for error in errors:
            provider_type = "Primary" if error["is_primary"] else "Fallback"
            summary_parts.append(
                f"{provider_type}({error['provider']}): {error['error_type']}"
            )

        return "; ".join(summary_parts)

    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status of all configured providers

        Returns:
            Dictionary with provider status information
        """
        return {
            "total_providers": len(self.providers),
            "primary_provider": {
                "name": self.primary_provider.provider_name,
                "model": self.primary_provider.default_model
            },
            "fallback_providers": [
                {
                    "name": p.provider_name,
                    "model": p.default_model
                }
                for p in self.fallback_providers
            ],
            "timeout_seconds": self.provider_timeout,
            "max_retries": self.max_retries
        }

    async def generate_parallel(
        self,
        requests: List[Dict[str, Any]],
        **default_kwargs
    ) -> List[OrchestratorResponse]:
        """
        Generate multiple responses in parallel
        
        Processes multiple generation requests concurrently using asyncio.gather.
        Each request can specify its own prompt, system_prompt, config, and model.
        Common parameters can be passed via default_kwargs.
        
        Args:
            requests: List of request dictionaries, each containing:
                - prompt: str (required)
                - system_prompt: Optional[str]
                - config: Optional[GenerationConfig]
                - model: Optional[str]
                - Any other kwargs specific to that request
            **default_kwargs: Default parameters applied to all requests
                (can be overridden by individual request)
        
        Returns:
            List[OrchestratorResponse]: List of orchestrator responses in same order as requests
        
        Example:
            requests = [
                {"prompt": "Interpret card 1", "model": "claude-haiku"},
                {"prompt": "Interpret card 2", "model": "claude-haiku"},
                {"prompt": "Overall reading", "model": "claude-sonnet-4"}
            ]
            responses = await orchestrator.generate_parallel(requests)
        """
        if not requests:
            return []
        
        logger.info(
            f"[Orchestrator] Starting parallel generation of {len(requests)} requests"
        )
        
        async def _generate_one(request: Dict[str, Any]) -> OrchestratorResponse:
            """Generate a single response"""
            # Merge default kwargs with request-specific kwargs
            merged_kwargs = {**default_kwargs, **request}
            
            # Extract known parameters
            prompt = merged_kwargs.pop("prompt")
            system_prompt = merged_kwargs.pop("system_prompt", None)
            config = merged_kwargs.pop("config", None)
            model = merged_kwargs.pop("model", None)
            
            # Remaining kwargs are passed to generate()
            return await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                config=config,
                model=model,
                **merged_kwargs
            )
        
        # Execute all requests in parallel
        start_time = time.time()
        try:
            responses = await asyncio.gather(
                *[_generate_one(req) for req in requests],
                return_exceptions=True
            )
            
            elapsed = int((time.time() - start_time) * 1000)
            logger.info(
                f"[Orchestrator] ✓ Parallel generation completed: "
                f"{len(requests)} requests in {elapsed}ms"
            )
            
            # Check for exceptions and convert to OrchestratorResponse with error info
            result = []
            for idx, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(
                        f"[Orchestrator] ✗ Request {idx} failed: {response}"
                    )
                    # Create a failed response wrapper
                    # Note: This maintains the response structure but indicates failure
                    raise response  # Re-raise to maintain error handling behavior
                result.append(response)
            
            return result
            
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(
                f"[Orchestrator] ✗ Parallel generation failed after {elapsed}ms: {e}"
            )
            raise

    async def close_all(self):
        """Close all provider connections"""
        logger.info("[Orchestrator] Closing all provider connections...")

        for provider in self.providers:
            try:
                await provider.close()
                logger.debug(f"[Orchestrator] Closed {provider.provider_name}")
            except Exception as e:
                logger.warning(
                    f"[Orchestrator] Error closing {provider.provider_name}: {e}"
                )


class CachedAIOrchestrator(AIOrchestrator):
    """
    AI Orchestrator with caching layer

    Extends AIOrchestrator with Redis-based caching for AI responses.
    Implements TASK-020 caching requirements.

    Features:
    - Automatic cache check before AI generation
    - Automatic cache storage after successful generation
    - Cache hit/miss metrics tracking
    - 24-hour TTL by default
    """

    def __init__(
        self,
        providers: List[AIProvider],
        cache,  # AICache instance
        provider_timeout: int = 3,
        max_retries: int = 2,
        enable_caching: bool = True
    ):
        """
        Initialize cached orchestrator

        Args:
            providers: List of AI providers
            cache: AICache instance
            provider_timeout: Timeout per provider
            max_retries: Maximum retries per provider
            enable_caching: Whether to enable caching (default True)
        """
        super().__init__(providers, provider_timeout, max_retries)
        self.cache = cache
        self.enable_caching = enable_caching

        logger.info(
            f"[CachedOrchestrator] Initialized with caching "
            f"{'enabled' if enable_caching else 'disabled'}"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ) -> AIResponse:
        """
        Generate with caching layer

        Checks cache first, then generates if not cached.

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use
            use_cache: Whether to use cache for this request (default True)
            **kwargs: Additional parameters

        Returns:
            AIResponse (from cache or AI provider)
        """
        # Check if caching is enabled for this request
        use_cache = use_cache and self.enable_caching

        # Try cache first
        if use_cache:
            cached_response = self.cache.get(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                **kwargs
            )

            if cached_response:
                logger.info(
                    f"[CachedOrchestrator] ✓ Returning cached response "
                    f"(provider={cached_response.provider})"
                )
                return cached_response

        # Cache miss - generate new response
        logger.debug("[CachedOrchestrator] Cache miss, generating new response...")

        response = await super().generate(
            prompt=prompt,
            system_prompt=system_prompt,
            config=config,
            model=model,
            **kwargs
        )

        # Cache the response
        if use_cache:
            self.cache.set(
                response=response,
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                **kwargs
            )

        return response

    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get cache metrics

        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_metrics()

    def reset_cache_metrics(self):
        """Reset cache metrics"""
        self.cache.reset_metrics()

    def invalidate_cache(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Invalidate specific cached response

        Args:
            prompt: User prompt
            system_prompt: System instruction
            model: Model name
            **kwargs: Additional parameters

        Returns:
            True if invalidated, False otherwise
        """
        return self.cache.invalidate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )

    def clear_all_cache(self) -> int:
        """
        Clear all cached responses

        Returns:
            Number of cached items deleted
        """
        return self.cache.clear_all()

    def get_cache_health(self) -> Dict[str, Any]:
        """
        Get cache health status

        Returns:
            Health status dictionary
        """
        return self.cache.health_check()

    async def close_all(self):
        """Close all connections including cache"""
        await super().close_all()
        self.cache.close()
        logger.info("[CachedOrchestrator] Cache connection closed")
