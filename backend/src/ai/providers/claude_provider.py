"""
Anthropic Claude Provider Implementation

Implements AIProvider interface for Anthropic's Claude models
"""
import time
from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic, APIError, RateLimitError, AuthenticationError as AnthropicAuthError, APITimeoutError

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


class ClaudeProvider(AIProvider):
    """
    Anthropic Claude API provider implementation

    Supports:
    - Claude 3 Opus, Sonnet, Haiku
    - Token counting (from API response)
    - Cost estimation
    - Comprehensive error handling
    """

    # Model pricing (per 1M tokens) - as of 2024
    MODEL_PRICING = {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
        "claude-sonnet-4-5-20250929": {"input": 4.0, "output": 20.0},
        "claude-haiku-4-5-20251001": {"input": 1.0, "output": 3.0},
        # Generic versions (map to latest)
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    }

    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-sonnet-4-5-20250929",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Claude provider

        Args:
            api_key: Anthropic API key
            default_model: Default model to use
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__(api_key, default_model, timeout, max_retries)

        self.client = AsyncAnthropic(
            api_key=api_key,
            timeout=timeout,
            max_retries=0  # We handle retries ourselves
        )

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def available_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-5-sonnet",
            "claude-3-haiku",
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
        Generate text using Anthropic's API

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use (overrides default)
            **kwargs: Additional Anthropic-specific parameters

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
        messages = [{"role": "user", "content": prompt}]

        # Build request parameters
        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }

        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = system_prompt

        # Add stop sequences if provided
        if config.stop_sequences:
            request_params["stop_sequences"] = config.stop_sequences

        # Add any additional kwargs
        request_params.update(kwargs)

        try:
            # Call Anthropic API
            response = await self.client.messages.create(**request_params)

            # Extract response data
            content = ""
            if response.content and len(response.content) > 0:
                # Claude returns content as a list of content blocks
                content = response.content[0].text

            finish_reason = response.stop_reason

            # Token usage
            usage = response.usage
            prompt_tokens = usage.input_tokens if usage else 0
            completion_tokens = usage.output_tokens if usage else 0
            total_tokens = prompt_tokens + completion_tokens

            # Estimate cost
            estimated_cost = self.estimate_cost(prompt_tokens, completion_tokens, model)

            # Calculate latency
            latency_ms = self._track_latency(start_time)

            return AIResponse(
                content=content,
                model=response.model,
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
        except AnthropicAuthError as e:
            raise AIAuthenticationError(str(e), provider=self.provider_name)
        except APITimeoutError as e:
            raise AITimeoutError(str(e), provider=self.provider_name)
        except APIError as e:
            # Generic Anthropic API error
            error_message = str(e)

            if "overloaded" in error_message.lower() or "unavailable" in error_message.lower():
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
        sorted_models = sorted(self.MODEL_PRICING.keys(), key=len, reverse=True)
        for model_key in sorted_models:
            if model.startswith(model_key):
                pricing = self.MODEL_PRICING[model_key]
                break

        if pricing is None:
            # Default to Sonnet pricing if model not found
            pricing = self.MODEL_PRICING["claude-3-sonnet-20240229"]

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text

        Note: Claude doesn't provide a built-in tokenizer for client-side counting.
        This is an approximation based on character count.
        For accurate token counts, use the API response after generation.

        Args:
            text: Text to count tokens for
            model: Model to use (not used for Claude)

        Returns:
            Approximate number of tokens
        """
        # Rough approximation: ~4 characters per token for English
        # This is less accurate than OpenAI's tiktoken but good enough for estimates
        return len(text) // 4

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

        # All Claude 3 models have 200K context window
        context_windows = {
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
        }

        # Sort model keys by length (descending) to match more specific models first
        sorted_models = sorted(context_windows.keys(), key=len, reverse=True)
        for model_key in sorted_models:
            if model.startswith(model_key):
                return context_windows[model_key]

        # Default to 200K
        return 200000

    async def close(self):
        """Close the Anthropic client connection"""
        await self.client.close()
