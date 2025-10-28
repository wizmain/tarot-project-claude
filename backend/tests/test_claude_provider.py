"""
Unit tests for Claude Provider (TASK-017)

Tests verify:
- Claude provider initialization
- Text generation with Claude 3 models
- Token counting (approximation)
- Cost estimation
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Any

from src.ai.providers.claude_provider import ClaudeProvider
from src.ai import (
    AIResponse,
    GenerationConfig,
    ProviderFactory,
    AIRateLimitError,
    AIAuthenticationError,
    AITimeoutError,
)


@pytest.fixture
def claude_provider():
    """Create Claude provider instance for testing"""
    return ClaudeProvider(
        api_key="test-key-123",
        default_model="claude-3-sonnet-20240229"
    )


class TestClaudeProviderInitialization:
    """Test suite for Claude provider initialization"""

    def test_provider_initialization(self, claude_provider):
        """Test provider can be initialized"""
        assert claude_provider.api_key == "test-key-123"
        assert claude_provider.default_model == "claude-3-sonnet-20240229"
        assert claude_provider.provider_name == "anthropic"
        assert claude_provider.timeout == 30
        assert claude_provider.max_retries == 3

    def test_available_models(self, claude_provider):
        """Test available models list"""
        models = claude_provider.available_models

        assert "claude-3-opus-20240229" in models
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-haiku-20240307" in models
        assert "claude-3-opus" in models
        assert "claude-3-sonnet" in models
        assert "claude-3-haiku" in models
        assert len(models) >= 6

    def test_provider_metadata(self, claude_provider):
        """Test get_metadata returns correct information"""
        metadata = claude_provider.get_metadata()

        assert metadata["provider"] == "anthropic"
        assert metadata["default_model"] == "claude-3-sonnet-20240229"
        assert "claude-3-opus" in metadata["available_models"]


class TestClaudeProviderTokenCounting:
    """Test suite for token counting (approximation)"""

    def test_count_tokens_simple(self, claude_provider):
        """Test token counting with simple text"""
        text = "Hello, world!"
        token_count = claude_provider.count_tokens(text)

        # Approximate: ~4 chars per token
        expected = len(text) // 4
        assert token_count == expected

    def test_count_tokens_longer_text(self, claude_provider):
        """Test token counting with longer text"""
        text = "The Fool card represents new beginnings and opportunities."
        token_count = claude_provider.count_tokens(text)

        # Should be roughly length // 4
        expected = len(text) // 4
        assert token_count == expected

    def test_count_tokens_approximation(self, claude_provider):
        """Test that token counting is approximation"""
        # 100 characters should be ~25 tokens
        text = "a" * 100
        token_count = claude_provider.count_tokens(text)
        assert token_count == 25


class TestClaudeProviderCostEstimation:
    """Test suite for cost estimation"""

    def test_estimate_cost_opus(self, claude_provider):
        """Test cost estimation for Claude 3 Opus"""
        # Opus: $15/M input, $75/M output
        cost = claude_provider.estimate_cost(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            model="claude-3-opus-20240229"
        )

        expected = (1_000_000 / 1_000_000) * 15.0 + (1_000_000 / 1_000_000) * 75.0  # 90.0
        assert cost == expected

    def test_estimate_cost_sonnet(self, claude_provider):
        """Test cost estimation for Claude 3 Sonnet"""
        # Sonnet: $3/M input, $15/M output
        cost = claude_provider.estimate_cost(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            model="claude-3-sonnet-20240229"
        )

        expected = (1_000_000 / 1_000_000) * 3.0 + (1_000_000 / 1_000_000) * 15.0  # 18.0
        assert cost == expected

    def test_estimate_cost_haiku(self, claude_provider):
        """Test cost estimation for Claude 3 Haiku"""
        # Haiku: $0.25/M input, $1.25/M output
        cost = claude_provider.estimate_cost(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            model="claude-3-haiku-20240307"
        )

        expected = (1_000_000 / 1_000_000) * 0.25 + (1_000_000 / 1_000_000) * 1.25  # 1.5
        assert cost == expected

    def test_estimate_cost_small_usage(self, claude_provider):
        """Test cost estimation with small token counts"""
        cost = claude_provider.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=2000,
            model="claude-3-sonnet-20240229"
        )

        # Should be reasonable (1K input + 2K output with Sonnet pricing)
        # (1000/1M * $3) + (2000/1M * $15) = 0.003 + 0.03 = 0.033
        assert cost > 0
        assert cost == 0.033

    def test_estimate_cost_generic_model_name(self, claude_provider):
        """Test cost estimation with generic model names"""
        # Test with "claude-3-sonnet" (without date)
        cost = claude_provider.estimate_cost(
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            model="claude-3-sonnet"
        )

        # Should use Sonnet pricing
        expected = 3.0 + 15.0  # 18.0
        assert cost == expected


class TestClaudeProviderContextWindow:
    """Test suite for context window sizes"""

    def test_context_window_opus(self, claude_provider):
        """Test context window for Claude 3 Opus"""
        window = claude_provider.get_model_context_window("claude-3-opus-20240229")
        assert window == 200000

    def test_context_window_sonnet(self, claude_provider):
        """Test context window for Claude 3 Sonnet"""
        window = claude_provider.get_model_context_window("claude-3-sonnet-20240229")
        assert window == 200000

    def test_context_window_haiku(self, claude_provider):
        """Test context window for Claude 3 Haiku"""
        window = claude_provider.get_model_context_window("claude-3-haiku-20240307")
        assert window == 200000

    def test_context_window_default(self, claude_provider):
        """Test context window defaults to 200K"""
        window = claude_provider.get_model_context_window("unknown-model")
        assert window == 200000


class TestClaudeProviderGeneration:
    """Test suite for text generation (mocked)"""

    @pytest.mark.asyncio
    async def test_generate_basic(self, claude_provider):
        """Test basic text generation (mocked)"""
        # Mock the Anthropic API response
        mock_content = Mock()
        mock_content.text = "The Fool represents new beginnings"

        mock_usage = Mock()
        mock_usage.input_tokens = 20
        mock_usage.output_tokens = 10

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        mock_response.model_dump = Mock(return_value={})

        # Patch the client
        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(return_value=mock_response)
        ):
            response = await claude_provider.generate(
                prompt="Interpret The Fool card",
                system_prompt="You are a tarot reader"
            )

            assert isinstance(response, AIResponse)
            assert response.content == "The Fool represents new beginnings"
            assert response.provider == "anthropic"
            assert response.model == "claude-3-sonnet-20240229"
            assert response.prompt_tokens == 20
            assert response.completion_tokens == 10
            assert response.total_tokens == 30
            assert response.estimated_cost > 0

    @pytest.mark.asyncio
    async def test_generate_with_custom_config(self, claude_provider):
        """Test generation with custom configuration"""
        mock_content = Mock()
        mock_content.text = "Test response"

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        mock_response.model_dump = Mock(return_value={})

        config = GenerationConfig(
            temperature=0.9,
            max_tokens=500,
            top_p=0.95
        )

        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(return_value=mock_response)
        ) as mock_create:
            await claude_provider.generate(
                prompt="Test prompt",
                config=config
            )

            # Verify config was passed correctly
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['temperature'] == 0.9
            assert call_kwargs['max_tokens'] == 500
            assert call_kwargs['top_p'] == 0.95

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self, claude_provider):
        """Test generation with custom model"""
        mock_content = Mock()
        mock_content.text = "Test"

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-haiku-20240307"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        mock_response.model_dump = Mock(return_value={})

        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(return_value=mock_response)
        ) as mock_create:
            response = await claude_provider.generate(
                prompt="Test",
                model="claude-3-haiku-20240307"
            )

            assert response.model == "claude-3-haiku-20240307"
            assert mock_create.call_args.kwargs['model'] == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, claude_provider):
        """Test generation with system prompt"""
        mock_content = Mock()
        mock_content.text = "Response"

        mock_usage = Mock()
        mock_usage.input_tokens = 15
        mock_usage.output_tokens = 5

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        mock_response.model_dump = Mock(return_value={})

        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(return_value=mock_response)
        ) as mock_create:
            await claude_provider.generate(
                prompt="Test",
                system_prompt="You are a helpful assistant"
            )

            # Verify system prompt was passed
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['system'] == "You are a helpful assistant"


class TestProviderFactoryIntegration:
    """Test suite for ProviderFactory integration"""

    def test_claude_provider_registered(self):
        """Test that Claude provider is registered in factory"""
        providers = ProviderFactory.list_providers()
        assert "anthropic" in providers

    def test_create_claude_provider_via_factory(self):
        """Test creating Claude provider via factory"""
        provider = ProviderFactory.create(
            provider_name="anthropic",
            api_key="test-key",
            default_model="claude-3-sonnet-20240229"
        )

        assert isinstance(provider, ClaudeProvider)
        assert provider.provider_name == "anthropic"
        assert provider.default_model == "claude-3-sonnet-20240229"


class TestClaudeProviderErrorHandling:
    """Test suite for error handling"""

    @pytest.mark.asyncio
    async def test_generate_handles_rate_limit_error(self, claude_provider):
        """Test that rate limit errors are properly handled"""
        from anthropic import RateLimitError

        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body=None))
        ):
            with pytest.raises(AIRateLimitError):
                await claude_provider.generate(prompt="Test")

    @pytest.mark.asyncio
    async def test_generate_handles_auth_error(self, claude_provider):
        """Test that authentication errors are properly handled"""
        from anthropic import AuthenticationError

        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(side_effect=AuthenticationError("Invalid API key", response=Mock(), body=None))
        ):
            with pytest.raises(AIAuthenticationError):
                await claude_provider.generate(prompt="Test")

    @pytest.mark.asyncio
    async def test_generate_handles_timeout_error(self, claude_provider):
        """Test that timeout errors are properly handled"""
        from anthropic import APITimeoutError

        with patch.object(
            claude_provider.client.messages,
            'create',
            new=AsyncMock(side_effect=APITimeoutError(request=Mock()))
        ):
            with pytest.raises(AITimeoutError):
                await claude_provider.generate(prompt="Test")
