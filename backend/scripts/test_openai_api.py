"""
Script to test OpenAI Provider with real API

This script requires OPENAI_API_KEY environment variable to be set.
Usage: python scripts/test_openai_api.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai import OpenAIProvider, ProviderFactory, GenerationConfig


async def test_openai_direct():
    """Test OpenAI provider directly"""
    print("=" * 60)
    print("Testing OpenAI Provider (Direct)")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='sk-...'")
        return False

    print(f"✓ API Key found (length: {len(api_key)})")

    # Create provider
    provider = OpenAIProvider(
        api_key=api_key,
        default_model="gpt-3.5-turbo"  # Use cheaper model for testing
    )

    print(f"✓ Provider initialized: {provider.provider_name}")
    print(f"  Default model: {provider.default_model}")
    print(f"  Available models: {len(provider.available_models)}")

    # Test token counting
    test_text = "The Fool card represents new beginnings and opportunities."
    token_count = provider.count_tokens(test_text)
    print(f"\n✓ Token counting works")
    print(f"  Text: '{test_text}'")
    print(f"  Tokens: {token_count}")

    # Test cost estimation
    cost = provider.estimate_cost(
        prompt_tokens=50,
        completion_tokens=100,
        model="gpt-3.5-turbo"
    )
    print(f"\n✓ Cost estimation works")
    print(f"  50 input + 100 output tokens")
    print(f"  Estimated cost: ${cost}")

    # Test generation
    print("\n🔄 Testing text generation...")
    try:
        response = await provider.generate(
            prompt="Interpret The Fool tarot card in one sentence.",
            system_prompt="You are a tarot card reader.",
            config=GenerationConfig(
                temperature=0.7,
                max_tokens=100
            )
        )

        print(f"✅ Generation successful!")
        print(f"  Content: {response.content}")
        print(f"  Model: {response.model}")
        print(f"  Tokens: {response.total_tokens} (prompt: {response.prompt_tokens}, completion: {response.completion_tokens})")
        print(f"  Cost: ${response.estimated_cost}")
        print(f"  Latency: {response.latency_ms}ms")
        print(f"  Finish reason: {response.finish_reason}")

        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False
    finally:
        await provider.close()


async def test_openai_via_factory():
    """Test OpenAI provider via factory"""
    print("\n" + "=" * 60)
    print("Testing OpenAI Provider (via ProviderFactory)")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False

    # Create via factory
    provider = ProviderFactory.create(
        provider_name="openai",
        api_key=api_key,
        default_model="gpt-3.5-turbo"
    )

    print(f"✓ Provider created via factory")
    print(f"  Type: {type(provider).__name__}")
    print(f"  Provider: {provider.provider_name}")

    # Quick test
    try:
        response = await provider.generate(
            prompt="What does The Tower card mean?",
            config=GenerationConfig(max_tokens=50)
        )

        print(f"✅ Generation via factory successful!")
        print(f"  Content: {response.content[:100]}...")
        print(f"  Cost: ${response.estimated_cost}")

        return True

    except Exception as e:
        print(f"❌ Generation via factory failed: {e}")
        return False
    finally:
        await provider.close()


async def test_error_handling():
    """Test error handling with invalid API key"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    # Test with invalid API key
    provider = OpenAIProvider(
        api_key="sk-invalid-key-for-testing",
        default_model="gpt-3.5-turbo"
    )

    print("✓ Testing with invalid API key...")

    try:
        await provider.generate(prompt="Test")
        print("❌ Should have raised authentication error")
        return False
    except Exception as e:
        error_type = type(e).__name__
        print(f"✅ Error properly caught: {error_type}")
        print(f"   Message: {str(e)[:100]}")
        return True
    finally:
        await provider.close()


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OpenAI Provider Test Suite")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Direct usage
    result1 = await test_openai_direct()
    results.append(("Direct Provider", result1))

    # Test 2: Factory usage
    result2 = await test_openai_via_factory()
    results.append(("Factory Provider", result2))

    # Test 3: Error handling
    result3 = await test_error_handling()
    results.append(("Error Handling", result3))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} tests passed")

    return all(r for _, r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
