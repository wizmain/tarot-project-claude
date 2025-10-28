"""
Unit tests for OpenAI Provider (TASK-016)

Tests verify:
- OpenAI provider initialization
- Text generation with GPT models
- Token counting with tiktoken
- Cost estimation
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Any

from src.ai.providers.openai_provider import OpenAIProvider
from src.ai import (
    AIResponse,
    GenerationConfig,
    ProviderFactory,
    AIRateLimitError,
    AIAuthenticationError,
    AITimeoutError,
)


@pytest.fixture
def openai_provider():
    """Create OpenAI provider instance for testing"""
    return OpenAIProvider(
        api_key="test-key-123",
        default_model="gpt-4-turbo-preview"
    )


class TestOpenAIProviderInitialization:
    """Test suite for OpenAI provider initialization"""

    def test_provider_initialization(self, openai_provider):
        """Test provider can be initialized"""
        assert openai_provider.api_key == "test-key-123"
        assert openai_provider.default_model == "gpt-4-turbo-preview"
        assert openai_provider.provider_name == "openai"
        assert openai_provider.timeout == 30
        assert openai_provider.max_retries == 3

    def test_available_models(self, openai_provider):
        """Test available models list"""
        models = openai_provider.available_models

        assert "gpt-4" in models
        assert "gpt-4-turbo-preview" in models
        assert "gpt-3.5-turbo" in models
        assert len(models) >= 8

    def test_provider_metadata(self, openai_provider):
        """Test get_metadata returns correct information"""
        metadata = openai_provider.get_metadata()

        assert metadata["provider"] == "openai"
        assert metadata["default_model"] == "gpt-4-turbo-preview"
        assert "gpt-4" in metadata["available_models"]


class TestOpenAIProviderTokenCounting:
    """Test suite for token counting"""

    def test_count_tokens_simple(self, openai_provider):
        """Test token counting with simple text"""
        text = "Hello, world!"
        token_count = openai_provider.count_tokens(text)

        # "Hello, world!" should be around 4 tokens
        assert token_count > 0
        assert token_count < 10

    def test_count_tokens_longer_text(self, openai_provider):
        """Test token counting with longer text"""
        text = "The Fool card represents new beginnings and opportunities."
        token_count = openai_provider.count_tokens(text)

        # Should be more than simple text
        assert token_count > 5
        assert token_count < 30

    def test_count_tokens_with_different_model(self, openai_provider):
        """Test token counting with specific model"""
        text = "Test message"

        count_gpt4 = openai_provider.count_tokens(text, model="gpt-4")
        count_gpt35 = openai_provider.count_tokens(text, model="gpt-3.5-turbo")

        # Should use same encoding (cl100k_base) so counts should be equal
        assert count_gpt4 == count_gpt35

    def test_encoder_caching(self, openai_provider):
        """Test that encoders are cached"""
        text = "Test"

        # First call creates encoder
        openai_provider.count_tokens(text, model="gpt-4")

        # Second call should use cached encoder
        assert "gpt-4" in openai_provider._encoders


class TestOpenAIProviderCostEstimation:
    """Test suite for cost estimation"""

    def test_estimate_cost_gpt4(self, openai_provider):
        """Test cost estimation for GPT-4"""
        # GPT-4: $0.03/1K input, $0.06/1K output
        cost = openai_provider.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="gpt-4"
        )

        expected = (1000 / 1000) * 0.03 + (1000 / 1000) * 0.06  # 0.09
        assert cost == expected

    def test_estimate_cost_gpt4_turbo(self, openai_provider):
        """Test cost estimation for GPT-4 Turbo"""
        # GPT-4 Turbo: $0.01/1K input, $0.03/1K output
        cost = openai_provider.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="gpt-4-turbo-preview"
        )

        expected = (1000 / 1000) * 0.01 + (1000 / 1000) * 0.03  # 0.04
        assert cost == expected

    def test_estimate_cost_gpt35_turbo(self, openai_provider):
        """Test cost estimation for GPT-3.5 Turbo"""
        # GPT-3.5 Turbo: $0.0005/1K input, $0.0015/1K output
        cost = openai_provider.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=1000,
            model="gpt-3.5-turbo"
        )

        expected = (1000 / 1000) * 0.0005 + (1000 / 1000) * 0.0015  # 0.002
        assert cost == expected

    def test_estimate_cost_small_usage(self, openai_provider):
        """Test cost estimation with small token counts"""
        cost = openai_provider.estimate_cost(
            prompt_tokens=50,
            completion_tokens=100,
            model="gpt-4-turbo-preview"
        )

        # Should be very small
        assert cost > 0
        assert cost < 0.01


class TestOpenAIProviderContextWindow:
    """Test suite for context window sizes"""

    def test_context_window_gpt4(self, openai_provider):
        """Test context window for GPT-4"""
        window = openai_provider.get_model_context_window("gpt-4")
        assert window == 8192

    def test_context_window_gpt4_turbo(self, openai_provider):
        """Test context window for GPT-4 Turbo"""
        window = openai_provider.get_model_context_window("gpt-4-turbo-preview")
        assert window == 128000

    def test_context_window_gpt35_turbo(self, openai_provider):
        """Test context window for GPT-3.5 Turbo"""
        window = openai_provider.get_model_context_window("gpt-3.5-turbo")
        assert window == 4096

    def test_context_window_unknown_model(self, openai_provider):
        """Test context window for unknown model defaults to smallest"""
        window = openai_provider.get_model_context_window("unknown-model")
        assert window == 4096


class TestOpenAIProviderGeneration:
    """Test suite for text generation (mocked)"""

    @pytest.mark.asyncio
    async def test_generate_basic(self, openai_provider):
        """Test basic text generation (mocked)"""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(content="The Fool represents new beginnings"),
                finish_reason="stop"
            )
        ]
        mock_response.usage = Mock(
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30
        )
        mock_response.model_dump = Mock(return_value={})

        # Patch the client
        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            new=AsyncMock(return_value=mock_response)
        ):
            response = await openai_provider.generate(
                prompt="Interpret The Fool card",
                system_prompt="You are a tarot reader"
            )

            assert isinstance(response, AIResponse)
            assert response.content == "The Fool represents new beginnings"
            assert response.provider == "openai"
            assert response.model == "gpt-4-turbo-preview"
            assert response.prompt_tokens == 20
            assert response.completion_tokens == 10
            assert response.total_tokens == 30
            assert response.estimated_cost > 0

    @pytest.mark.asyncio
    async def test_generate_with_custom_config(self, openai_provider):
        """Test generation with custom configuration"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test"), finish_reason="stop")]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_response.model_dump = Mock(return_value={})

        config = GenerationConfig(
            temperature=0.9,
            max_tokens=500,
            top_p=0.95
        )

        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            new=AsyncMock(return_value=mock_response)
        ) as mock_create:
            await openai_provider.generate(
                prompt="Test prompt",
                config=config
            )

            # Verify config was passed correctly
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['temperature'] == 0.9
            assert call_kwargs['max_tokens'] == 500
            assert call_kwargs['top_p'] == 0.95

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self, openai_provider):
        """Test generation with custom model"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test"), finish_reason="stop")]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_response.model_dump = Mock(return_value={})

        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            new=AsyncMock(return_value=mock_response)
        ) as mock_create:
            response = await openai_provider.generate(
                prompt="Test",
                model="gpt-3.5-turbo"
            )

            assert response.model == "gpt-3.5-turbo"
            assert mock_create.call_args.kwargs['model'] == "gpt-3.5-turbo"


class TestProviderFactoryIntegration:
    """Test suite for ProviderFactory integration"""

    def test_openai_provider_registered(self):
        """Test that OpenAI provider is registered in factory"""
        providers = ProviderFactory.list_providers()
        assert "openai" in providers

    def test_create_openai_provider_via_factory(self):
        """Test creating OpenAI provider via factory"""
        provider = ProviderFactory.create(
            provider_name="openai",
            api_key="test-key",
            default_model="gpt-4"
        )

        assert isinstance(provider, OpenAIProvider)
        assert provider.provider_name == "openai"
        assert provider.default_model == "gpt-4"


class TestOpenAIProviderErrorHandling:
    """Test suite for error handling"""

    @pytest.mark.asyncio
    async def test_generate_handles_rate_limit_error(self, openai_provider):
        """Test that rate limit errors are properly handled"""
        from openai import RateLimitError

        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            new=AsyncMock(side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body=None))
        ):
            with pytest.raises(AIRateLimitError):
                await openai_provider.generate(prompt="Test")

    @pytest.mark.asyncio
    async def test_generate_handles_auth_error(self, openai_provider):
        """Test that authentication errors are properly handled"""
        from openai import AuthenticationError

        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            new=AsyncMock(side_effect=AuthenticationError("Invalid API key", response=Mock(), body=None))
        ):
            with pytest.raises(AIAuthenticationError):
                await openai_provider.generate(prompt="Test")

    @pytest.mark.asyncio
    async def test_generate_handles_timeout_error(self, openai_provider):
        """Test that timeout errors are properly handled"""
        from openai import APITimeoutError

        with patch.object(
            openai_provider.client.chat.completions,
            'create',
            new=AsyncMock(side_effect=APITimeoutError(request=Mock()))
        ):
            with pytest.raises(AITimeoutError):
                await openai_provider.generate(prompt="Test")
