"""
AI Provider 기본 클래스 및 인터페이스 모듈

이 모듈의 목적:
- 모든 AI Provider의 공통 인터페이스 정의
- OpenAI, Anthropic 등 다양한 AI 서비스 통합 지원
- 일관된 에러 핸들링 및 재시도 로직
- 토큰 사용량 추적 및 비용 계산

구현해야 하는 주요 메서드:
- generate(): 프롬프트를 받아 AI 응답 생성
- estimate_cost(): 예상 비용 계산
- count_tokens(): 토큰 개수 카운팅

TASK-015: AI Provider 인터페이스 설계 구현
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import logging

from src.ai.models import (
    AIResponse,
    AIProviderError,
    AIRateLimitError,
    AIAuthenticationError,
    AIInvalidRequestError,
    AITimeoutError,
    AIServiceUnavailableError,
    GenerationConfig,
    TokenUsage
)

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """
    AI Provider 추상 베이스 클래스

    모든 AI Provider(OpenAI, Claude 등)가 상속받아야 하는 인터페이스입니다.
    이를 통해 Provider 간 일관된 API를 제공하고 교체 가능성을 보장합니다.

    구현 예시:
        class MyAIProvider(AIProvider):
            async def generate(self, prompt, **kwargs):
                # 구현
                pass

            def estimate_cost(self, input_tokens, output_tokens):
                # 구현
                pass
    """

    def __init__(
        self,
        api_key: str,
        default_model: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize AI provider

        Args:
            api_key: API key for the provider
            default_model: Default model to use for generation
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self._validate_api_key()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Provider name (e.g., 'openai', 'anthropic')

        Returns:
            Provider identifier string
        """
        pass

    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """
        List of available models for this provider

        Returns:
            List of model identifiers
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate text using the AI provider

        Args:
            prompt: User prompt/message
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use (overrides default)
            **kwargs: Additional provider-specific parameters

        Returns:
            AIResponse object with generated content and metadata

        Raises:
            AIProviderError: If generation fails
            AIRateLimitError: If rate limit is exceeded
            AIAuthenticationError: If authentication fails
            AIInvalidRequestError: If request is invalid
            AITimeoutError: If request times out
            AIServiceUnavailableError: If service is unavailable
        """
        pass

    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """
        Estimate cost for a generation request

        Args:
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion
            model: Model used (uses default if not specified)

        Returns:
            Estimated cost in USD
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text for the specified model

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Number of tokens
        """
        pass

    def validate_config(self, config: GenerationConfig) -> None:
        """
        Validate generation configuration

        Args:
            config: Configuration to validate

        Raises:
            AIInvalidRequestError: If configuration is invalid
        """
        # Pydantic already validates ranges, but we can add custom logic
        if config.max_tokens <= 0:
            raise AIInvalidRequestError(
                "max_tokens must be positive",
                provider=self.provider_name
            )

        if config.temperature < 0 or config.temperature > 2:
            raise AIInvalidRequestError(
                "temperature must be between 0 and 2",
                provider=self.provider_name
            )

    def _validate_api_key(self) -> None:
        """
        Validate API key format

        Raises:
            AIAuthenticationError: If API key is invalid
        """
        if not self.api_key or len(self.api_key.strip()) == 0:
            raise AIAuthenticationError(
                "API key is empty or invalid",
                provider=self.provider_name
            )

    def _validate_model(self, model: str) -> None:
        """
        Validate that model is available for this provider

        Args:
            model: Model identifier to validate

        Raises:
            AIInvalidRequestError: If model is not available
        """
        if model not in self.available_models:
            raise AIInvalidRequestError(
                f"Model '{model}' not available. Available models: {', '.join(self.available_models)}",
                provider=self.provider_name
            )

    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate with automatic retry on transient failures

        Args:
            prompt: User prompt/message
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            AIResponse object

        Raises:
            AIProviderError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"[{self.provider_name}] Generation attempt {attempt + 1}/{self.max_retries}"
                )

                response = await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    config=config,
                    model=model,
                    **kwargs
                )

                return response

            except (AIRateLimitError, AIServiceUnavailableError, AITimeoutError) as e:
                last_error = e

                # Calculate backoff delay
                backoff_delay = min(2 ** attempt, 10)  # Max 10 seconds

                if hasattr(e, 'retry_after') and e.retry_after:
                    backoff_delay = e.retry_after

                logger.warning(
                    f"[{self.provider_name}] Transient error: {e}. "
                    f"Retrying in {backoff_delay}s (attempt {attempt + 1}/{self.max_retries})"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(backoff_delay)
                    continue
                else:
                    raise

            except (AIAuthenticationError, AIInvalidRequestError) as e:
                # Don't retry on non-transient errors
                logger.error(f"[{self.provider_name}] Non-retryable error: {e}")
                raise

        # Should never reach here, but just in case
        if last_error:
            raise last_error

        raise AIProviderError(
            "Failed to generate after all retries",
            provider=self.provider_name,
            error_type="MAX_RETRIES_EXCEEDED"
        )

    def _track_latency(self, start_time: float) -> int:
        """
        Calculate request latency in milliseconds

        Args:
            start_time: Start time from time.time()

        Returns:
            Latency in milliseconds
        """
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        return latency_ms

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name}, model={self.default_model})"

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get provider metadata

        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.provider_name,
            "default_model": self.default_model,
            "available_models": self.available_models,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }


class ProviderFactory:
    """
    Factory for creating AI provider instances
    """

    _providers: Dict[str, type] = {}

    @classmethod
    def register(cls, provider_name: str, provider_class: type):
        """
        Register a provider class

        Args:
            provider_name: Provider identifier
            provider_class: Provider class (must inherit from AIProvider)
        """
        if not issubclass(provider_class, AIProvider):
            raise TypeError(f"{provider_class} must inherit from AIProvider")

        cls._providers[provider_name] = provider_class
        logger.info(f"Registered AI provider: {provider_name}")

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        **kwargs
    ) -> AIProvider:
        """
        Create a provider instance

        Args:
            provider_name: Provider identifier (e.g., 'openai', 'anthropic')
            api_key: API key for the provider
            **kwargs: Additional provider-specific arguments

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not registered
        """
        if provider_name not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not registered. "
                f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(api_key=api_key, **kwargs)

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        Get list of registered providers

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())
