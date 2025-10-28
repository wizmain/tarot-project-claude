"""
AI Providers Module

Provides concrete implementations of AIProvider for different services
"""
from src.ai.providers.openai_provider import OpenAIProvider
from src.ai.providers.claude_provider import ClaudeProvider
from src.ai.provider import ProviderFactory

# Auto-register providers
ProviderFactory.register("openai", OpenAIProvider)
ProviderFactory.register("anthropic", ClaudeProvider)

__all__ = [
    "OpenAIProvider",
    "ClaudeProvider",
]
