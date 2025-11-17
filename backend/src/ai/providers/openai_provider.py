"""
OpenAI Provider 구현 모듈

이 모듈의 목적:
- OpenAI GPT 모델을 타로 리딩 서비스에 통합
- tiktoken을 활용한 정확한 토큰 카운팅
- 모델별 비용 계산 (GPT-4, GPT-4 Turbo 등)
- OpenAI API 에러를 통합 에러 시스템으로 변환

지원 모델:
- GPT-4: 최고 품질의 응답, 높은 비용
- GPT-4 Turbo: 빠른 속도와 낮은 비용
- GPT-3.5 Turbo: 빠르고 저렴한 대안

주요 기능:
- System/User 프롬프트 분리 지원
- 스트리밍 응답 가능 (추후 구현)
- Rate Limit 및 Timeout 에러 핸들링
- 1K 토큰당 비용 자동 계산

TASK-016: OpenAI Provider 구현
"""
import time
import logging
from typing import List, Optional, Dict, Any
import tiktoken
from openai import AsyncOpenAI, OpenAIError, RateLimitError, AuthenticationError as OpenAIAuthError, APITimeoutError

from src.ai.provider import AIProvider
from src.ai.models import (
    AIResponse,
    AIProviderError,
    AIRateLimitError,
    AIAuthenticationError,
    AIInvalidRequestError,
    AITimeoutError,
    AIServiceUnavailableError,
    GenerationConfig,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI GPT 모델 Provider

    OpenAI의 Chat Completions API를 사용하여 타로 리딩 응답을 생성합니다.
    tiktoken 라이브러리로 토큰 수를 정확히 계산하고 비용을 추정합니다.

    사용 예시:
        provider = OpenAIProvider(
            api_key="sk-...",
            default_model="gpt-4-turbo-preview"
        )
        response = await provider.generate(
            system_prompt="당신은 타로 전문가입니다.",
            user_prompt="The Fool 카드를 해석해주세요."
        )
    """

    # Model pricing (per 1K tokens) - Updated 2025
    # Source: https://openai.com/api/pricing/
    MODEL_PRICING = {
        # GPT-5 Series (Latest - Oct 2025)
        "gpt-5": {"input": 0.02, "output": 0.08},  # Estimated
        "gpt-5-2025-08-07": {"input": 0.02, "output": 0.08},
        "gpt-5-pro": {"input": 0.04, "output": 0.16},  # Estimated
        "gpt-5-pro-2025-10-06": {"input": 0.04, "output": 0.16},
        "gpt-5-mini": {"input": 0.0003, "output": 0.0012},  # Estimated
        "gpt-5-mini-2025-08-07": {"input": 0.0003, "output": 0.0012},
        "gpt-5-nano": {"input": 0.0001, "output": 0.0004},  # Estimated
        "gpt-5-nano-2025-08-07": {"input": 0.0001, "output": 0.0004},

        # GPT-4.1 Series (Apr 2025)
        "gpt-4.1": {"input": 0.015, "output": 0.06},  # Estimated
        "gpt-4.1-2025-04-14": {"input": 0.015, "output": 0.06},
        "gpt-4.1-mini": {"input": 0.0002, "output": 0.0008},  # Estimated
        "gpt-4.1-mini-2025-04-14": {"input": 0.0002, "output": 0.0008},
        "gpt-4.1-nano": {"input": 0.00008, "output": 0.00032},  # Estimated - most cost-efficient
        "gpt-4.1-nano-2025-04-14": {"input": 0.00008, "output": 0.00032},

        # GPT-4o Series
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o-2024-11-20": {"input": 0.0025, "output": 0.01},
        "gpt-4o-2024-08-06": {"input": 0.0025, "output": 0.01},
        "gpt-4o-2024-05-13": {"input": 0.005, "output": 0.015},

        # GPT-4 Turbo
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-2024-04-09": {"input": 0.01, "output": 0.03},
        "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},

        # GPT-4
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-0613": {"input": 0.03, "output": 0.06},

        # O-series (Reasoning models)
        "o1": {"input": 0.015, "output": 0.06},
        "o1-2024-12-17": {"input": 0.015, "output": 0.06},
        "o1-mini": {"input": 0.003, "output": 0.012},
        "o1-mini-2024-09-12": {"input": 0.003, "output": 0.012},
        "o1-pro": {"input": 0.06, "output": 0.24},  # Pro tier
        "o1-pro-2025-03-19": {"input": 0.06, "output": 0.24},
        "o3": {"input": 0.02, "output": 0.08},
        "o3-2025-04-16": {"input": 0.02, "output": 0.08},
        "o3-mini": {"input": 0.0011, "output": 0.0044},
        "o3-mini-2025-01-31": {"input": 0.0011, "output": 0.0044},
        "o4-mini": {"input": 0.001, "output": 0.004},
        "o4-mini-2025-04-16": {"input": 0.001, "output": 0.004},

        # GPT-3.5 Turbo
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
        "gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.002},
    }

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4-turbo-preview",
        timeout: int = 30,
        max_retries: int = 3,
        organization: Optional[str] = None
    ):
        """
        Initialize OpenAI provider

        Args:
            api_key: OpenAI API key
            default_model: Default model to use
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            organization: Optional organization ID
        """
        super().__init__(api_key, default_model, timeout, max_retries)

        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=0,  # We handle retries ourselves
            organization=organization
        )

        # Cache for tiktoken encoders
        self._encoders: Dict[str, tiktoken.Encoding] = {}

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def available_models(self) -> List[str]:
        """
        Available chat completion models from OpenAI
        Updated: 2025-10-31
        Note: This is a reference list. Unknown models will be validated by OpenAI API.
        """
        return [
            # GPT-5 Series (Latest)
            "gpt-5",
            "gpt-5-pro",
            "gpt-5-mini",
            "gpt-5-nano",
            # "gpt-5-2025-08-07",
            # "gpt-5-mini-2025-08-07",
            # "gpt-5-nano-2025-08-07",

            # GPT-4.1 Series
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            # "gpt-4.1-2025-04-14",
            # "gpt-4.1-mini-2025-04-14",
            # "gpt-4.1-nano-2025-04-14",

            # GPT-4o Series
            "gpt-4o",
            "gpt-4o-mini",
            # "gpt-4o-2024-11-20",
            # "gpt-4o-2024-08-06",
            # "gpt-4o-2024-05-13",
            # "gpt-4o-mini-2024-07-18",

            # GPT-4 Turbo
            "gpt-4-turbo",
            # "gpt-4-turbo-preview",
            # "gpt-4-turbo-2024-04-09",
            # "gpt-4-0125-preview",
            # "gpt-4-1106-preview",

            # GPT-4
            "gpt-4",
            "gpt-4-0613",

            # O-series (Reasoning models)
            "o1",
            "o1-mini",
            # "o1-2024-12-17",
            # "o1-mini-2024-09-12",
            "o1-pro",
            # "o1-pro-2025-03-19",
            "o3",
            "o3-mini",
            # "o3-2025-04-16",
            # "o3-mini-2025-01-31",
            "o4-mini",
            # "o4-mini-2025-04-16",

            # GPT-3.5 Turbo
            "gpt-3.5-turbo",
            # "gpt-3.5-turbo-0125",
            # "gpt-3.5-turbo-1106",
            # "gpt-3.5-turbo-instruct",
            # "gpt-3.5-turbo-instruct-0914",
        ]

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate text using OpenAI's API

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use (overrides default)
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            AIResponse object

        Raises:
            Various AIProviderError subclasses
        """
        start_time = time.time()

        # Use default config if not provided
        if config is None:
            config = GenerationConfig()

        # Use default model if not specified
        if model is None:
            model = self.default_model

        # Validate model
        self._validate_model(model)

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            logger.info(
                "[OpenAI] Sending request model=%s max_tokens=%s temperature=%.2f timeout=%ss",
                model,
                config.max_tokens,
                config.temperature,
                self.timeout,
            )
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences,
                **kwargs
            )

            # Extract response data
            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason

            # Token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            # Estimate cost
            estimated_cost = self.estimate_cost(prompt_tokens, completion_tokens, model)

            # Calculate latency
            latency_ms = self._track_latency(start_time)

            return AIResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                finish_reason=finish_reason,
                latency_ms=latency_ms,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )

        except RateLimitError as e:
            raise AIRateLimitError(
                str(e),
                provider=self.provider_name,
                retry_after=getattr(e, 'retry_after', None)
            )
        except OpenAIAuthError as e:
            raise AIAuthenticationError(str(e), provider=self.provider_name)
        except APITimeoutError as e:
            raise AITimeoutError(str(e), provider=self.provider_name)
        except OpenAIError as e:
            # Generic OpenAI error
            error_message = str(e)

            if "service_unavailable" in error_message.lower():
                raise AIServiceUnavailableError(error_message, provider=self.provider_name)
            elif "invalid" in error_message.lower():
                raise AIInvalidRequestError(error_message, provider=self.provider_name)
            else:
                raise AIProviderError(
                    error_message,
                    provider=self.provider_name,
                    error_type="UNKNOWN",
                    original_error=e
                )
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error: {str(e)}",
                provider=self.provider_name,
                error_type="UNEXPECTED",
                original_error=e
            )

    def _validate_model(self, model: str) -> None:
        """
        Validate model - warn if unknown but let OpenAI API do the actual validation

        This allows using new models without code changes while still providing
        helpful warnings for potential typos.

        Args:
            model: Model identifier to validate
        """
        if model not in self.available_models:
            logger.warning(
                f"[OpenAI] Model '{model}' not in known list. "
                f"Known models: {', '.join(self.available_models)}. "
                f"Proceeding anyway - OpenAI API will validate."
            )

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
        if model is None:
            model = self.default_model

        # Get pricing for model (check longer names first to avoid prefix collisions)
        pricing = None
        # Sort model keys by length (descending) to match more specific models first
        sorted_models = sorted(self.MODEL_PRICING.keys(), key=len, reverse=True)
        for model_key in sorted_models:
            if model.startswith(model_key):
                pricing = self.MODEL_PRICING[model_key]
                break

        if pricing is None:
            # Default to GPT-4 pricing if model not found
            logger.warning(f"[OpenAI] Unknown model '{model}' for pricing. Using gpt-4 pricing as fallback.")
            pricing = self.MODEL_PRICING["gpt-4"]

        # Calculate cost (pricing is per 1K tokens)
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text using tiktoken

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Number of tokens
        """
        if model is None:
            model = self.default_model

        # Get or create encoder
        encoder = self._get_encoder(model)

        # Count tokens
        tokens = encoder.encode(text)
        return len(tokens)

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """
        Get tiktoken encoder for model (with caching)

        Args:
            model: Model identifier

        Returns:
            Tiktoken encoding instance
        """
        if model not in self._encoders:
            try:
                # Try to get encoding for specific model
                self._encoders[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fall back to cl100k_base (used by GPT-4 and GPT-3.5-turbo)
                self._encoders[model] = tiktoken.get_encoding("cl100k_base")

        return self._encoders[model]

    def get_model_context_window(self, model: Optional[str] = None) -> int:
        """
        Get context window size for model

        Args:
            model: Model identifier

        Returns:
            Context window size in tokens
        """
        if model is None:
            model = self.default_model

        # Context windows by model
        context_windows = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4-turbo-preview": 128000,
            "gpt-4-0125-preview": 128000,
            "gpt-4-1106-preview": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-0125": 16385,
            "gpt-3.5-turbo-1106": 16385,
        }

        # Sort model keys by length (descending) to match more specific models first
        sorted_models = sorted(context_windows.keys(), key=len, reverse=True)
        for model_key in sorted_models:
            if model.startswith(model_key):
                return context_windows[model_key]

        # Default to smallest window
        return 4096

    async def close(self):
        """Close the OpenAI client connection"""
        await self.client.close()
