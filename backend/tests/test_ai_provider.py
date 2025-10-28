"""
Unit tests for AI Provider Base Class (TASK-015)

Tests verify:
- Abstract interface definition
- Provider factory registration
- Error handling hierarchy
- Configuration validation
"""
import pytest
from typing import List, Optional

from src.ai import (
    AIProvider,
    ProviderFactory,
    AIResponse,
    GenerationConfig,
    AIProviderError,
    AIAuthenticationError,
    AIInvalidRequestError,
)


class MockAIProvider(AIProvider):
    """Mock provider for testing"""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def available_models(self) -> List[str]:
        return ["mock-model-1", "mock-model-2"]

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """Mock generation"""
        return AIResponse(
            content=f"Mock response to: {prompt[:50]}",
            model=model or self.default_model,
            provider=self.provider_name,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            estimated_cost=0.001,
            finish_reason="stop",
            latency_ms=100
        )

    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """Mock cost estimation"""
        return (prompt_tokens * 0.00001) + (completion_tokens * 0.00002)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Mock token counting - simple word count"""
        return len(text.split())


class TestAIProviderInterface:
    """Test suite for AIProvider base class"""

    def test_provider_initialization(self):
        """Test provider can be initialized with valid API key"""
        provider = MockAIProvider(
            api_key="test-key-123",
            default_model="mock-model-1"
        )

        assert provider.api_key == "test-key-123"
        assert provider.default_model == "mock-model-1"
        assert provider.provider_name == "mock"
        assert provider.timeout == 30
        assert provider.max_retries == 3

    def test_provider_empty_api_key_raises_error(self):
        """Test that empty API key raises authentication error"""
        with pytest.raises(AIAuthenticationError):
            MockAIProvider(api_key="", default_model="mock-model-1")

    def test_provider_metadata(self):
        """Test get_metadata returns correct information"""
        provider = MockAIProvider(
            api_key="test-key",
            default_model="mock-model-1",
            timeout=60,
            max_retries=5
        )

        metadata = provider.get_metadata()

        assert metadata["provider"] == "mock"
        assert metadata["default_model"] == "mock-model-1"
        assert metadata["available_models"] == ["mock-model-1", "mock-model-2"]
        assert metadata["timeout"] == 60
        assert metadata["max_retries"] == 5

    @pytest.mark.asyncio
    async def test_generate_returns_ai_response(self):
        """Test generate method returns AIResponse"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        response = await provider.generate(
            prompt="Interpret The Fool card",
            system_prompt="You are a tarot reader"
        )

        assert isinstance(response, AIResponse)
        assert response.provider == "mock"
        assert response.model == "mock-model-1"
        assert len(response.content) > 0
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30

    def test_estimate_cost(self):
        """Test cost estimation"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        cost = provider.estimate_cost(prompt_tokens=100, completion_tokens=200)

        assert cost > 0
        assert isinstance(cost, float)
        # 100 * 0.00001 + 200 * 0.00002 = 0.005
        assert cost == 0.005

    def test_count_tokens(self):
        """Test token counting"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        tokens = provider.count_tokens("This is a test message")

        assert tokens == 5  # Simple word count

    def test_validate_config_valid(self):
        """Test config validation with valid config"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        config = GenerationConfig(
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9
        )

        # Should not raise
        provider.validate_config(config)

    def test_validate_model_valid(self):
        """Test model validation with valid model"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        # Should not raise
        provider._validate_model("mock-model-1")
        provider._validate_model("mock-model-2")

    def test_validate_model_invalid(self):
        """Test model validation with invalid model"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        with pytest.raises(AIInvalidRequestError, match="not available"):
            provider._validate_model("invalid-model")

    def test_provider_repr(self):
        """Test string representation"""
        provider = MockAIProvider(api_key="test-key", default_model="mock-model-1")

        repr_str = repr(provider)

        assert "MockAIProvider" in repr_str
        assert "provider=mock" in repr_str
        assert "model=mock-model-1" in repr_str


class TestProviderFactory:
    """Test suite for ProviderFactory"""

    def test_register_provider(self):
        """Test registering a provider"""
        ProviderFactory.register("mock", MockAIProvider)

        providers = ProviderFactory.list_providers()
        assert "mock" in providers

    def test_register_invalid_provider_raises_error(self):
        """Test that registering non-AIProvider class raises error"""
        class NotAProvider:
            pass

        with pytest.raises(TypeError, match="must inherit from AIProvider"):
            ProviderFactory.register("invalid", NotAProvider)

    def test_create_provider(self):
        """Test creating a provider via factory"""
        ProviderFactory.register("mock", MockAIProvider)

        provider = ProviderFactory.create(
            provider_name="mock",
            api_key="test-key",
            default_model="mock-model-1"
        )

        assert isinstance(provider, MockAIProvider)
        assert provider.provider_name == "mock"
        assert provider.api_key == "test-key"

    def test_create_unregistered_provider_raises_error(self):
        """Test creating unregistered provider raises error"""
        with pytest.raises(ValueError, match="not registered"):
            ProviderFactory.create(
                provider_name="nonexistent",
                api_key="test-key"
            )

    def test_list_providers(self):
        """Test listing registered providers"""
        ProviderFactory.register("mock", MockAIProvider)

        providers = ProviderFactory.list_providers()

        assert isinstance(providers, list)
        assert "mock" in providers


class TestGenerationConfig:
    """Test suite for GenerationConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = GenerationConfig()

        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stop_sequences is None

    def test_custom_config(self):
        """Test custom configuration"""
        config = GenerationConfig(
            temperature=0.9,
            max_tokens=2000,
            top_p=0.95,
            stop_sequences=["END", "STOP"]
        )

        assert config.temperature == 0.9
        assert config.max_tokens == 2000
        assert config.top_p == 0.95
        assert config.stop_sequences == ["END", "STOP"]

    def test_config_validation_temperature_out_of_range(self):
        """Test that invalid temperature raises validation error"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            GenerationConfig(temperature=3.0)

    def test_config_validation_max_tokens_negative(self):
        """Test that negative max_tokens raises validation error"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            GenerationConfig(max_tokens=-100)


class TestAIResponse:
    """Test suite for AIResponse model"""

    def test_ai_response_creation(self):
        """Test creating AIResponse"""
        response = AIResponse(
            content="The Fool represents new beginnings",
            model="gpt-4",
            provider="openai",
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150,
            estimated_cost=0.01,
            finish_reason="stop",
            latency_ms=500
        )

        assert response.content == "The Fool represents new beginnings"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.total_tokens == 150
        assert response.estimated_cost == 0.01

    def test_ai_response_with_minimal_fields(self):
        """Test AIResponse with only required fields"""
        response = AIResponse(
            content="Test content",
            model="test-model",
            provider="test"
        )

        assert response.content == "Test content"
        assert response.prompt_tokens is None
        assert response.estimated_cost is None
        assert response.created_at is not None  # Auto-generated
