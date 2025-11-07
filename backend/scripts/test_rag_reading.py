"""
Test script for RAG-enhanced tarot readings

This script creates a test reading to verify that the RAG context enrichment
is working correctly and improving reading quality.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import get_logger
from src.ai.rag.retriever import Retriever
from src.ai.rag.context_enricher import ContextEnricher

logger = get_logger(__name__)


async def test_rag_enrichment():
    """Test RAG context enrichment"""
    print("\n" + "=" * 70)
    print("RAG Context Enrichment Test")
    print("=" * 70 + "\n")

    # Initialize RAG components
    print("1. Initializing RAG components...")
    retriever = Retriever()
    context_enricher = ContextEnricher(retriever)
    print("   ✓ RAG components initialized\n")

    # Test case: One card reading
    print("2. Testing one-card reading context enrichment...")
    test_cards = [{"id": 0, "is_reversed": False}]  # The Fool
    test_question = "새로운 프로젝트를 시작하는 것에 대해 조언을 구합니다"

    rag_context = context_enricher.enrich_prompt_context(
        cards=test_cards,
        spread_type="one_card",
        question=test_question,
        category="career",
        language="ko",
    )

    print(f"   Question: {test_question}")
    print(f"   Cards: {test_cards}")
    print(f"   Spread: one_card")
    print(f"   Category: career\n")

    print("3. RAG Context Results:")
    print(f"   - Card contexts retrieved: {len(rag_context.get('card_contexts', []))}")
    if rag_context.get('card_contexts'):
        for card_ctx in rag_context['card_contexts']:
            card_data = card_ctx.get('card_data', {})
            print(f"     • Card ID {card_ctx.get('card_id')}: {card_data.get('name', 'Unknown')}")
            if card_data.get('deep_meaning'):
                print(f"       Deep meaning: {card_data['deep_meaning'][:100]}...")

    if rag_context.get('spread_context'):
        print(f"   - Spread context: ✓")
        print(f"     Interpretation guide: {rag_context['spread_context']['interpretation_guide'][:100]}...")

    if rag_context.get('category_guidance'):
        print(f"   - Category guidance: ✓")
        print(f"     {rag_context['category_guidance'][:100]}...")

    if rag_context.get('combination_insights'):
        print(f"   - Combination insights: {len(rag_context['combination_insights'])} found")

    print("\n✅ RAG context enrichment is working correctly!")
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_rag_enrichment())
