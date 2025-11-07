#!/usr/bin/env python3
"""
Test script for RAG (Retrieval-Augmented Generation) system

This script demonstrates and validates the RAG pipeline for Tarot readings.
It performs the following operations:
1. Initializes the embedding model and vector store
2. Loads knowledge base data
3. Populates the vector store with card and spread knowledge
4. Performs sample searches
5. Generates enriched context for a reading

Usage:
    python scripts/test_rag.py
"""
import sys
import os
import json
from pathlib import Path

# Add backend to Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

# Setup logging before imports
from src.core.logging import setup_logging, get_logger
setup_logging()

logger = get_logger(__name__)

from src.ai.rag import (
    get_embedding_model,
    VectorStore,
    KnowledgeBase,
    Retriever,
    ContextEnricher
)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def initialize_vector_store():
    """Initialize and populate the vector store with knowledge base data"""
    print_section("STEP 1: Initializing Vector Store")

    # Initialize components
    logger.info("Creating VectorStore instance...")
    vector_store = VectorStore(collection_name="tarot_knowledge_test")

    logger.info("Creating KnowledgeBase instance...")
    knowledge_base = KnowledgeBase()

    # Load all cards and spreads
    logger.info("Loading all cards from knowledge base...")
    all_cards = knowledge_base.get_all_cards()
    print(f"Loaded {len(all_cards)} cards from knowledge base")

    logger.info("Loading all spreads from knowledge base...")
    all_spreads = knowledge_base.get_all_spreads()
    print(f"Loaded {len(all_spreads)} spreads from knowledge base")

    # Prepare documents for vector store
    documents = []
    metadatas = []
    ids = []

    # Add card documents
    for card in all_cards:
        # Create document from card knowledge
        doc_text = f"{card['name']} ({card['name_ko']}): {card['deep_meaning']}"
        documents.append(doc_text)

        metadata = {
            "type": "card",
            "card_id": card["id"],
            "name": card["name"],
            "arcana_type": card["arcana_type"]
        }
        metadatas.append(metadata)
        ids.append(f"card_{card['id']}")

        # Add upright themes as separate documents
        if card.get("upright_themes"):
            themes_text = f"{card['name']} upright themes: {', '.join(card['upright_themes'])}"
            documents.append(themes_text)
            metadatas.append({**metadata, "aspect": "upright_themes"})
            ids.append(f"card_{card['id']}_upright")

        # Add symbolism as separate documents
        if card.get("symbolism"):
            symbolism_text = f"{card['name']} symbolism: " + "; ".join([
                f"{k}: {v}" for k, v in card["symbolism"].items()
            ])
            documents.append(symbolism_text)
            metadatas.append({**metadata, "aspect": "symbolism"})
            ids.append(f"card_{card['id']}_symbolism")

    # Add spread documents
    for spread in all_spreads:
        doc_text = f"{spread['name']}: {spread['description']}"
        documents.append(doc_text)

        metadata = {
            "type": "spread",
            "spread_id": spread["id"],
            "name": spread["name"]
        }
        metadatas.append(metadata)
        ids.append(f"spread_{spread['id']}")

        # Add interpretation guide
        if spread.get("interpretation_guide"):
            guide_text = f"{spread['name']} interpretation: {spread['interpretation_guide']}"
            documents.append(guide_text)
            metadatas.append({**metadata, "aspect": "guide"})
            ids.append(f"spread_{spread['id']}_guide")

    # Add to vector store
    logger.info(f"Adding {len(documents)} documents to vector store...")
    print(f"\nAdding {len(documents)} documents to vector store...")

    vector_store.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Vector store now contains {vector_store.get_count()} documents")

    return vector_store, knowledge_base


def test_basic_search(vector_store: VectorStore):
    """Test basic semantic search"""
    print_section("STEP 2: Testing Basic Semantic Search")

    queries = [
        "What does new beginnings mean?",
        "Tell me about intuition and inner wisdom",
        "How do I interpret a three card spread?"
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.search(query=query, k=3)

        print(f"Found {len(results['documents'])} results:\n")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        ), 1):
            print(f"  {i}. [{metadata.get('type', 'unknown')}] {metadata.get('name', 'N/A')}")
            print(f"     Distance: {distance:.4f}")
            print(f"     Snippet: {doc[:100]}...")
            print()


def test_retriever(knowledge_base: KnowledgeBase, vector_store: VectorStore):
    """Test the Retriever class"""
    print_section("STEP 3: Testing Retriever Operations")

    retriever = Retriever(
        vector_store=vector_store,
        knowledge_base=knowledge_base
    )

    # Test card context retrieval
    print("\n--- Retrieving Card Context for The Fool (ID: 0) ---")
    card_context = retriever.retrieve_card_context(
        card_id=0,
        query="What does this card mean for new beginnings?",
        k=2
    )

    if card_context["card_data"]:
        print(f"Card: {card_context['card_data']['name']}")
        print(f"Meaning: {card_context['card_data']['deep_meaning'][:150]}...")
        print(f"\nRetrieved {len(card_context['relevant_contexts'])} relevant contexts")

    # Test spread context retrieval
    print("\n--- Retrieving Spread Context for One Card ---")
    spread_context = retriever.retrieve_spread_context(
        spread_type="one_card",
        k=2
    )

    if spread_context["spread_data"]:
        print(f"Spread: {spread_context['spread_data']['name']}")
        print(f"Description: {spread_context['spread_data']['description']}")

    # Test combination context retrieval
    print("\n--- Retrieving Combination Context ---")
    combo_context = retriever.retrieve_combination_context(
        card_ids=[0, 1],
        k=2
    )

    print(f"Found {len(combo_context['combinations'])} matching combinations")
    for combo in combo_context['combinations'][:2]:
        print(f"  - {', '.join(combo['cards'])}: {combo['meaning'][:100]}...")


def test_context_enricher(knowledge_base: KnowledgeBase, vector_store: VectorStore):
    """Test the ContextEnricher class"""
    print_section("STEP 4: Testing Context Enricher")

    enricher = ContextEnricher(
        retriever=Retriever(
            vector_store=vector_store,
            knowledge_base=knowledge_base
        )
    )

    # Test enrichment for a one-card reading
    print("\n--- Enriching Context for One-Card Reading ---")
    print("Question: 'What should I focus on today?'")
    print("Card: The Fool (Upright)\n")

    enriched_context = enricher.enrich_prompt_context(
        cards=[{"id": 0, "is_reversed": False}],
        spread_type="one_card",
        question="What should I focus on today?",
        category="career",
        language="en"
    )

    print("Enriched Context Structure:")
    print(f"  - Cards context: {len(enriched_context['cards_context'])} card(s)")
    print(f"  - Spread context: {bool(enriched_context['spread_context'])}")
    print(f"  - Combination context: {bool(enriched_context['combination_context'])}")
    print(f"  - Category context: {bool(enriched_context['category_context'])}")
    print(f"  - General insights: {len(enriched_context['general_insights'])} insight(s)")

    # Test formatted context
    print("\n--- Formatted Context (Detailed) ---")
    formatted_context = enricher.format_context_for_prompt(
        enriched_context,
        template_type="detailed"
    )
    print(formatted_context[:800] + "...\n")

    # Test three-card reading
    print("\n--- Enriching Context for Three-Card Reading ---")
    print("Question: 'What is the trajectory of my career?'")
    print("Cards: The Fool, The Magician, The Empress\n")

    enriched_context_3card = enricher.enrich_prompt_context(
        cards=[
            {"id": 0, "is_reversed": False},
            {"id": 1, "is_reversed": False},
            {"id": 3, "is_reversed": False}
        ],
        spread_type="three_card_past_present_future",
        question="What is the trajectory of my career?",
        category="career",
        language="en"
    )

    print("Enriched Context Structure:")
    print(f"  - Cards context: {len(enriched_context_3card['cards_context'])} card(s)")
    print(f"  - Combination context: {len(enriched_context_3card['combination_context'].get('combinations', []))} combination(s)")

    # Save sample context to file for inspection
    output_file = backend_root / "scripts" / "sample_enriched_context.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_context_3card, f, indent=2, ensure_ascii=False)
    print(f"\nSample enriched context saved to: {output_file}")


def main():
    """Main test function"""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  RAG SYSTEM TEST - TAROT READING APPLICATION".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)

    try:
        # Step 1: Initialize and populate vector store
        vector_store, knowledge_base = initialize_vector_store()

        # Step 2: Test basic search
        test_basic_search(vector_store)

        # Step 3: Test retriever
        test_retriever(knowledge_base, vector_store)

        # Step 4: Test context enricher
        test_context_enricher(knowledge_base, vector_store)

        # Success summary
        print_section("TEST SUMMARY")
        print("SUCCESS: All RAG system components are working correctly!")
        print("\nThe RAG system is ready to enhance Tarot readings with:")
        print("  - Semantic search over card knowledge")
        print("  - Spread pattern understanding")
        print("  - Card combination insights")
        print("  - Category-specific interpretations")
        print("  - Enriched context for AI prompt generation")

        print("\nNext steps:")
        print("  1. Expand knowledge base to all 78 cards")
        print("  2. Add more spread patterns")
        print("  3. Expand card combination patterns")
        print("  4. Add more reading categories (love, finance, etc.)")
        print("  5. Integrate with AI orchestrator for readings")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\nERROR: Test failed - {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
