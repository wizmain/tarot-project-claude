"""
AI Module - Unified interface for AI providers

This module provides a consistent interface for working with multiple AI providers
(OpenAI, Anthropic Claude, etc.) for tarot reading interpretations.

Usage:
    from src.ai import AIProvider, ProviderFactory, AIResponse

    # Create provider using factory
    provider = ProviderFactory.create('openai', api_key='...')

    # Generate text
    response = await provider.generate(
        prompt="Interpret The Fool card...",
        system_prompt="You are a tarot reader..."
    )
"""

# Data models
from src.ai.models import (
    AIResponse,
    AIProviderError,
    AIRateLimitError,
    AIAuthenticationError,
    AIInvalidRequestError,
    AITimeoutError,
    AIServiceUnavailableError,
    TokenUsage,
    GenerationConfig,
)

# Base provider and factory
from src.ai.provider import (
    AIProvider,
    ProviderFactory,
)

# Orchestrator and caching
from src.ai.orchestrator import (
    AIOrchestrator,
    CachedAIOrchestrator,
)
from src.ai.cache import (
    AICache,
    AICacheMetrics,
)

# Concrete providers (auto-registers in ProviderFactory)
from src.ai.providers import (
    OpenAIProvider,
    ClaudeProvider,
    GeminiProvider,
)

__all__ = [
    # Data models
    "AIResponse",
    "TokenUsage",
    "GenerationConfig",

    # Error types
    "AIProviderError",
    "AIRateLimitError",
    "AIAuthenticationError",
    "AIInvalidRequestError",
    "AITimeoutError",
    "AIServiceUnavailableError",

    # Provider classes
    "AIProvider",
    "ProviderFactory",
    "AIOrchestrator",
    "CachedAIOrchestrator",

    # Caching
    "AICache",
    "AICacheMetrics",

    # Concrete providers
    "OpenAIProvider",
    "ClaudeProvider",
    "GeminiProvider",
]
