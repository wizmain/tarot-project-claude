"""
Gemini Provider 구현 모듈

이 모듈의 목적:
- Google Gemini 모델을 타로 리딩 서비스에 통합
- Gemini API를 활용한 텍스트 생성
- 모델별 비용 계산 및 토큰 추정
- Gemini API 에러를 통합 에러 시스템으로 변환

지원 모델:
- Gemini 2.0 Flash: 최신 고속 모델
- Gemini 1.5 Pro: 고성능 모델
- Gemini 1.5 Flash: 빠르고 효율적인 모델

주요 기능:
- System/User 프롬프트 분리 지원
- Rate Limit 및 Timeout 에러 핸들링
- 토큰당 비용 자동 계산
"""
import time
import logging
from typing import List, Optional, Dict, Any

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    from google.api_core import exceptions as google_exceptions
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None
    google_exceptions = None

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


class GeminiProvider(AIProvider):
    """
    Google Gemini 모델 Provider

    Google의 Generative AI API를 사용하여 타로 리딩 응답을 생성합니다.
    토큰 기반 비용 계산을 지원합니다.

    사용 예시:
        provider = GeminiProvider(
            api_key="AIza...",
            default_model="gemini-2.0-flash-exp"
        )
        response = await provider.generate(
            system_prompt="당신은 타로 전문가입니다.",
            user_prompt="The Fool 카드를 해석해주세요."
        )
    """

    # Model pricing (per 1M tokens) - Updated 2024
    # Source: https://ai.google.dev/pricing
    MODEL_PRICING = {
        # Gemini 2.5
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},  # Per 1M tokens (same as 1.5 Pro)
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},  # Per 1M tokens (same as 1.5 Flash)
        "gemini-2.5-flash-lite": {"input": 0.0375, "output": 0.15},  # Per 1M tokens (same as 1.5 Flash 8b)
        
        # Gemini 2.0
        "gemini-2.0-flash": {"input": 0.0, "output": 0.0},  # Free during preview
        "gemini-2.0-flash-lite": {"input": 0.0, "output": 0.0},  # Free during preview
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free during preview
        "gemini-2.0-flash-thinking-exp": {"input": 0.0, "output": 0.0},  # Free during preview
        
        # Gemini 1.5 Pro
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},  # Per 1M tokens
        "gemini-1.5-pro-001": {"input": 1.25, "output": 5.00},
        "gemini-1.5-pro-002": {"input": 1.25, "output": 5.00},
        "gemini-1.5-pro-latest": {"input": 1.25, "output": 5.00},  # Same as base model
        
        # Gemini 1.5 Flash
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},  # Per 1M tokens
        "gemini-1.5-flash-001": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash-002": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash-8b": {"input": 0.0375, "output": 0.15},  # Per 1M tokens
        "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},  # Same as base model
        
        # Gemini 1.0 Pro (Legacy)
        "gemini-1.0-pro": {"input": 0.50, "output": 1.50},  # Per 1M tokens
        "gemini-1.0-pro-001": {"input": 0.50, "output": 1.50},
        "gemini-pro": {"input": 0.50, "output": 1.50},
    }

    def __init__(
        self,
        api_key: str,
        default_model: str = "gemini-2.0-flash-lite",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Gemini provider

        Args:
            api_key: Google AI API key
            default_model: Default model to use
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install it with: pip install google-generativeai"
            )

        super().__init__(api_key, default_model, timeout, max_retries)

        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Safety settings - allow creative content for tarot readings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def available_models(self) -> List[str]:
        """
        Available Gemini models
        Updated: 2024-12-20
        """
        return [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
            # Gemini 2.0 (Latest)
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash-thinking-exp",
            
            # Gemini 1.5 Pro
            "gemini-1.5-pro",
            "gemini-1.5-pro-001",
            "gemini-1.5-pro-002",
            "gemini-1.5-pro-latest",
            
            # Gemini 1.5 Flash
            "gemini-1.5-flash",
            "gemini-1.5-flash-001",
            "gemini-1.5-flash-002",
            "gemini-1.5-flash-8b",
            "gemini-1.5-flash-latest",
            
            # Gemini 1.0 Pro (Legacy)
            "gemini-1.0-pro",
            "gemini-1.0-pro-001",
            "gemini-pro",
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
        Generate text using Gemini API

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            config: Generation configuration
            model: Model to use (overrides default)
            **kwargs: Additional Gemini-specific parameters

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

        try:
            logger.info(
                "[Gemini] Sending request model=%s max_tokens=%s temperature=%.2f timeout=%ss",
                model,
                config.max_tokens,
                config.temperature,
                self.timeout,
            )

            # Initialize model (without system_instruction for compatibility)
            gemini_model = genai.GenerativeModel(
                model_name=model,
                safety_settings=self.safety_settings,
            )

            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
                stop_sequences=config.stop_sequences if config.stop_sequences else None,
            )

            # Combine system prompt with user prompt if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate content
            response = await gemini_model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                request_options={"timeout": self.timeout},
            )

            # Extract response data safely
            # Check finish_reason first to handle MAX_TOKENS and SAFETY blocks
            finish_reason = None
            content = ""
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason_raw = candidate.finish_reason
                
                # Convert Gemini finish_reason enum to standardized string
                # 0: FINISH_REASON_UNSPECIFIED -> None
                # 1: STOP -> "stop"
                # 2: MAX_TOKENS -> "max_tokens"
                # 3: SAFETY -> "safety"
                # 4: RECITATION -> "recitation"
                # 5: OTHER -> "other"
                finish_reason_map = {
                    0: None,  # FINISH_REASON_UNSPECIFIED
                    1: "stop",  # STOP
                    2: "max_tokens",  # MAX_TOKENS
                    3: "safety",  # SAFETY
                    4: "recitation",  # RECITATION
                    5: "other",  # OTHER
                }
                
                # Handle enum value (int) or string representation
                if isinstance(finish_reason_raw, int):
                    finish_reason = finish_reason_map.get(finish_reason_raw)
                elif isinstance(finish_reason_raw, str):
                    # Try to parse string representation
                    try:
                        finish_reason_int = int(finish_reason_raw)
                        finish_reason = finish_reason_map.get(finish_reason_int)
                    except ValueError:
                        finish_reason = finish_reason_raw.lower() if finish_reason_raw else None
                else:
                    finish_reason = str(finish_reason_raw) if finish_reason_raw else None
                
                # Try to extract content from parts
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        # Extract text from parts
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        content = ''.join(text_parts)
                
                # If no content from parts, try response.text (but handle errors)
                if not content:
                    try:
                        if hasattr(response, 'text'):
                            content = response.text
                    except Exception as e:
                        # finish_reason이 MAX_TOKENS(2) 또는 SAFETY(3)일 때
                        # response.text에 접근하면 오류가 발생할 수 있음
                        logger.warning(
                            f"[Gemini] Failed to access response.text: {e}. "
                            f"finish_reason={finish_reason}. "
                            f"Content may be empty or truncated."
                        )
                        content = ""
                
            # Token usage (Gemini provides usage metadata)
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', 0)
            
            # Log warning if content is empty but finish_reason indicates truncation
            if not content and finish_reason == "max_tokens":
                logger.warning(
                    f"[Gemini] Response truncated due to max_tokens limit. "
                    f"finish_reason={finish_reason}, "
                    f"completion_tokens={completion_tokens}, "
                    f"max_output_tokens={config.max_tokens}. "
                    f"Consider increasing max_output_tokens."
                )

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
                raw_response=None  # Gemini response objects are not directly serializable
            )

        except google_exceptions.ResourceExhausted as e:
            raise AIRateLimitError(
                str(e),
                provider=self.provider_name,
                retry_after=None
            )
        except google_exceptions.Unauthenticated as e:
            raise AIAuthenticationError(str(e), provider=self.provider_name)
        except google_exceptions.DeadlineExceeded as e:
            raise AITimeoutError(str(e), provider=self.provider_name)
        except google_exceptions.ServiceUnavailable as e:
            raise AIServiceUnavailableError(str(e), provider=self.provider_name)
        except google_exceptions.InvalidArgument as e:
            raise AIInvalidRequestError(str(e), provider=self.provider_name)
        except Exception as e:
            error_message = str(e)
            
            # Check for specific error patterns
            if "quota" in error_message.lower() or "rate limit" in error_message.lower():
                raise AIRateLimitError(error_message, provider=self.provider_name)
            elif "unauthorized" in error_message.lower() or "authentication" in error_message.lower():
                raise AIAuthenticationError(error_message, provider=self.provider_name)
            elif "timeout" in error_message.lower():
                raise AITimeoutError(error_message, provider=self.provider_name)
            else:
                raise AIProviderError(
                    f"Unexpected error: {error_message}",
                    provider=self.provider_name,
                    error_type="UNEXPECTED",
                    original_error=e
                )

    def _validate_model(self, model: str) -> None:
        """
        Validate model - warn if unknown but let Gemini API do the actual validation

        Args:
            model: Model identifier to validate
        """
        if model not in self.available_models:
            logger.warning(
                f"[Gemini] Model '{model}' not in known list. "
                f"Known models: {', '.join(self.available_models)}. "
                f"Proceeding anyway - Gemini API will validate."
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

        # Get pricing for model
        pricing = None
        sorted_models = sorted(self.MODEL_PRICING.keys(), key=len, reverse=True)
        for model_key in sorted_models:
            if model.startswith(model_key):
                pricing = self.MODEL_PRICING[model_key]
                break

        if pricing is None:
            # Default to gemini-1.5-flash pricing if model not found
            logger.warning(
                f"[Gemini] Unknown model '{model}' for pricing. "
                f"Using gemini-1.5-flash pricing as fallback."
            )
            pricing = self.MODEL_PRICING["gemini-1.5-flash"]

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text using Gemini's count_tokens API

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            Number of tokens (estimated if API call fails)
        """
        if model is None:
            model = self.default_model

        try:
            # Use Gemini's token counting
            gemini_model = genai.GenerativeModel(model_name=model)
            result = gemini_model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.warning(f"[Gemini] Token counting failed: {e}. Using estimation.")
            # Fallback: rough estimation (1 token ≈ 4 characters for English)
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

        # Context windows by model
        context_windows = {
            "gemini-2.0-flash": 1_048_576,  # 1M tokens
            "gemini-1.5-pro": 2_097_152,  # 2M tokens
            "gemini-1.5-flash": 1_048_576,  # 1M tokens
            "gemini-1.5-flash-8b": 1_048_576,  # 1M tokens
            "gemini-1.0-pro": 32_768,  # 32K tokens
            "gemini-pro": 32_768,  # 32K tokens
        }

        sorted_models = sorted(context_windows.keys(), key=len, reverse=True)
        for model_key in sorted_models:
            if model.startswith(model_key):
                return context_windows[model_key]

        # Default to smallest window
        return 32_768

    async def close(self):
        """Close the Gemini client connection (no-op for Gemini)"""
        pass

