"""
AI Provider Data Models

Defines data structures used across all AI providers
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AIResponse(BaseModel):
    """
    Standard response format from AI providers
    """
    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider name (openai, anthropic, etc)")

    # Usage statistics
    prompt_tokens: Optional[int] = Field(None, description="Number of tokens in prompt")
    completion_tokens: Optional[int] = Field(None, description="Number of tokens in completion")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")

    # Cost estimation
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")

    # Metadata
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: Optional[int] = Field(None, description="Response latency in milliseconds")

    # Raw response (for debugging)
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw API response")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "The Fool card represents new beginnings...",
                "model": "gpt-4-turbo-preview",
                "provider": "openai",
                "prompt_tokens": 150,
                "completion_tokens": 200,
                "total_tokens": 350,
                "estimated_cost": 0.0105,
                "finish_reason": "stop",
                "latency_ms": 1250
            }
        }


class AIProviderError(Exception):
    """
    Base exception for AI provider errors
    """
    def __init__(
        self,
        message: str,
        provider: str,
        error_type: str,
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.provider = provider
        self.error_type = error_type
        self.original_error = original_error
        self.retry_after = retry_after
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.provider}] {self.error_type}: {self.message}"


class AIRateLimitError(AIProviderError):
    """Raised when API rate limit is exceeded"""
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="RATE_LIMIT",
            retry_after=retry_after
        )


class AIAuthenticationError(AIProviderError):
    """Raised when API authentication fails"""
    def __init__(self, message: str, provider: str):
        super().__init__(
            message=message,
            provider=provider,
            error_type="AUTHENTICATION"
        )


class AIInvalidRequestError(AIProviderError):
    """Raised when request is invalid"""
    def __init__(self, message: str, provider: str):
        super().__init__(
            message=message,
            provider=provider,
            error_type="INVALID_REQUEST"
        )


class AITimeoutError(AIProviderError):
    """Raised when request times out"""
    def __init__(self, message: str, provider: str):
        super().__init__(
            message=message,
            provider=provider,
            error_type="TIMEOUT"
        )


class AIServiceUnavailableError(AIProviderError):
    """Raised when AI service is unavailable"""
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            provider=provider,
            error_type="SERVICE_UNAVAILABLE",
            retry_after=retry_after
        )


class TokenUsage(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")

    @property
    def cost_usd(self) -> float:
        """
        Estimate cost in USD (will be overridden by provider-specific implementations)
        """
        return 0.0


class GenerationConfig(BaseModel):
    """Configuration for text generation"""
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(1000, ge=1, le=4096, description="Maximum tokens to generate")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop_sequences: Optional[list[str]] = Field(None, description="Stop sequences")

    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }
        }
