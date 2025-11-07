"""
Retriever for RAG System

This module provides high-level retrieval operations for card knowledge,
spread patterns, and card combinations using vector similarity search.

Classes:
    Retriever: Main retrieval interface for the RAG system

Phase 2 Optimization: Added async methods for parallel RAG queries
Phase 3 Optimization: Added LRU caching for repeated queries
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from functools import partial

from .vector_store import VectorStore
from .knowledge_base import KnowledgeBase
from .cache import get_rag_cache

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retriever for semantic search over Tarot knowledge

    This class provides convenient methods for retrieving relevant context
    from the knowledge base using vector similarity search.

    Attributes:
        vector_store: VectorStore instance for similarity search
        knowledge_base: KnowledgeBase instance for loading data
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        enable_cache: bool = True
    ):
        """
        Initialize the retriever

        Args:
            vector_store: VectorStore instance (creates new if None)
            knowledge_base: KnowledgeBase instance (creates new if None)
            enable_cache: Enable RAG query caching (Phase 3 optimization)
        """
        self.vector_store = vector_store or VectorStore()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.enable_cache = enable_cache
        
        # Phase 3: Initialize cache
        if enable_cache:
            self.cache = get_rag_cache()
            logger.info("Retriever initialized with caching enabled")
        else:
            self.cache = None
            logger.info("Retriever initialized (caching disabled)")

    def retrieve_card_context(
        self,
        card_id: int,
        query: str,
        k: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for a specific card (Phase 3: with caching)

        Args:
            card_id: Card ID to retrieve context for
            query: Query text to find relevant information
            k: Number of similar documents to retrieve

        Returns:
            Dictionary containing:
                - card_data: Full card knowledge from knowledge base
                - relevant_contexts: List of relevant text snippets
                - sources: Metadata about retrieved documents

        Example:
            >>> retriever = Retriever()
            >>> context = retriever.retrieve_card_context(
            ...     card_id=0,
            ...     query="What does The Fool mean for new beginnings?",
            ...     k=3
            ... )
        """
        # Phase 3: Check cache first
        if self.cache:
            cache_key_params = {
                "method": "retrieve_card_context",
                "card_id": card_id,
                "query": query[:100],  # Truncate long queries
                "k": k
            }
            cached_result = self.cache.get(**cache_key_params)
            if cached_result:
                return cached_result
        
        result = {
            "card_data": None,
            "relevant_contexts": [],
            "sources": []
        }

        try:
            # Load full card knowledge
            card_data = self.knowledge_base.load_card_knowledge(card_id)
            result["card_data"] = card_data

            if not card_data:
                logger.warning(f"No card data found for ID: {card_id}")
                return result

            # Search for relevant contexts
            search_results = self.vector_store.search(
                query=query,
                k=k,
                filter_dict={"card_id": card_id}
            )

            result["relevant_contexts"] = search_results["documents"]
            result["sources"] = search_results["metadatas"]

            logger.debug(f"Retrieved {len(result['relevant_contexts'])} contexts for card {card_id}")
            
            # Phase 3: Cache the result
            if self.cache:
                self.cache.set(result, **cache_key_params)

        except Exception as e:
            logger.error(f"Failed to retrieve card context: {e}")

        return result

    def retrieve_spread_context(
        self,
        spread_type: str,
        k: int = 2
    ) -> Dict[str, Any]:
        """
        Retrieve context for a specific spread pattern (Phase 3: with caching)

        Args:
            spread_type: Spread identifier (e.g., "one_card", "three_card_past_present_future")
            k: Number of similar documents to retrieve

        Returns:
            Dictionary containing:
                - spread_data: Full spread knowledge from knowledge base
                - relevant_contexts: List of relevant text snippets
                - sources: Metadata about retrieved documents
        """
        # Phase 3: Check cache first (spread context rarely changes)
        if self.cache:
            cache_key_params = {
                "method": "retrieve_spread_context",
                "spread_type": spread_type,
                "k": k
            }
            cached_result = self.cache.get(**cache_key_params)
            if cached_result:
                return cached_result
        
        result = {
            "spread_data": None,
            "relevant_contexts": [],
            "sources": []
        }

        try:
            # Load full spread knowledge
            spread_data = self.knowledge_base.load_spread_knowledge(spread_type)
            result["spread_data"] = spread_data

            if not spread_data:
                logger.warning(f"No spread data found for: {spread_type}")
                return result

            # Search for relevant contexts
            query = f"How to interpret {spread_data.get('name', spread_type)} spread"
            search_results = self.vector_store.search(
                query=query,
                k=k,
                filter_dict={"type": "spread", "spread_id": spread_type}
            )

            result["relevant_contexts"] = search_results["documents"]
            result["sources"] = search_results["metadatas"]

            logger.debug(f"Retrieved {len(result['relevant_contexts'])} contexts for spread {spread_type}")
            
            # Phase 3: Cache the result (long TTL since spreads rarely change)
            if self.cache:
                self.cache.set(result, **cache_key_params)

        except Exception as e:
            logger.error(f"Failed to retrieve spread context: {e}")

        return result

    def retrieve_combination_context(
        self,
        card_ids: List[int],
        k: int = 2
    ) -> Dict[str, Any]:
        """
        Retrieve context for card combinations

        Args:
            card_ids: List of card IDs in the reading
            k: Number of similar combination patterns to retrieve

        Returns:
            Dictionary containing:
                - combinations: List of matching combination patterns
                - relevant_contexts: List of relevant text snippets
                - sources: Metadata about retrieved documents
        """
        result = {
            "combinations": [],
            "relevant_contexts": [],
            "sources": []
        }

        try:
            # Load combination knowledge
            combo_data = self.knowledge_base.load_combination_knowledge()

            if not combo_data:
                logger.warning("No combination data found")
                return result

            # Find matching combinations
            combinations_list = combo_data.get("combinations", [])
            for combo in combinations_list:
                combo_card_ids = combo.get("card_ids", [])
                # Check if any of our cards match this combination
                if any(cid in card_ids for cid in combo_card_ids):
                    result["combinations"].append(combo)

            # Search for relevant contexts
            card_names = [str(cid) for cid in card_ids]
            query = f"Card combination meaning: {', '.join(card_names)}"

            search_results = self.vector_store.search(
                query=query,
                k=k,
                filter_dict={"type": "combination"}
            )

            result["relevant_contexts"] = search_results["documents"]
            result["sources"] = search_results["metadatas"]

            logger.debug(f"Retrieved {len(result['combinations'])} combinations and {len(result['relevant_contexts'])} contexts")

        except Exception as e:
            logger.error(f"Failed to retrieve combination context: {e}")

        return result

    def retrieve_category_context(
        self,
        category: str,
        card_ids: List[int],
        k: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieve category-specific interpretation context

        Args:
            category: Reading category (e.g., "career", "love", "finance")
            card_ids: List of card IDs in the reading
            k: Number of relevant documents to retrieve

        Returns:
            Dictionary containing:
                - category_data: Category-specific knowledge from knowledge base
                - card_meanings: Category-specific meanings for the cards
                - relevant_contexts: List of relevant text snippets
        """
        result = {
            "category_data": None,
            "card_meanings": {},
            "relevant_contexts": []
        }

        try:
            # Load category knowledge
            category_data = self.knowledge_base.load_category_knowledge(category)
            result["category_data"] = category_data

            if not category_data:
                logger.warning(f"No category data found for: {category}")
                return result

            # Extract card-specific meanings for this category
            card_specific = category_data.get("card_specific_meanings", {})
            for card_id in card_ids:
                card_key = str(card_id)
                if card_key in card_specific:
                    result["card_meanings"][card_id] = card_specific[card_key]

            # Search for relevant contexts
            query = f"{category} reading interpretation"
            search_results = self.vector_store.search(
                query=query,
                k=k,
                filter_dict={"category": category}
            )

            result["relevant_contexts"] = search_results["documents"]

            logger.debug(f"Retrieved category context for {category}")

        except Exception as e:
            logger.error(f"Failed to retrieve category context: {e}")

        return result

    def retrieve_general_context(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve general context for any query (Phase 3: with caching)

        Args:
            query: Query text
            k: Number of similar documents to retrieve

        Returns:
            Dictionary containing:
                - documents: List of relevant text snippets
                - metadatas: List of metadata for each document
                - distances: Similarity distances
        """
        # Phase 3: Check cache first
        if self.cache:
            cache_key_params = {
                "method": "retrieve_general_context",
                "query": query[:100],  # Truncate long queries
                "k": k
            }
            cached_result = self.cache.get(**cache_key_params)
            if cached_result:
                return cached_result
        
        try:
            search_results = self.vector_store.search(query=query, k=k)
            logger.debug(f"Retrieved {len(search_results['documents'])} general contexts")
            
            # Phase 3: Cache the result
            if self.cache:
                self.cache.set(search_results, **cache_key_params)
            
            return search_results

        except Exception as e:
            logger.error(f"Failed to retrieve general context: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    # ========== ASYNC METHODS FOR PARALLEL EXECUTION (Phase 2 Optimization) ==========

    async def retrieve_card_context_async(
        self,
        card_id: int,
        query: str,
        k: int = 3
    ) -> Dict[str, Any]:
        """
        Async version of retrieve_card_context for parallel execution

        Runs the synchronous retrieval in a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.retrieve_card_context, card_id, query, k)
        )

    async def retrieve_spread_context_async(
        self,
        spread_type: str,
        k: int = 2
    ) -> Dict[str, Any]:
        """
        Async version of retrieve_spread_context for parallel execution
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.retrieve_spread_context, spread_type, k)
        )

    async def retrieve_combination_context_async(
        self,
        card_ids: List[int],
        k: int = 2
    ) -> Dict[str, Any]:
        """
        Async version of retrieve_combination_context for parallel execution
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.retrieve_combination_context, card_ids, k)
        )

    async def retrieve_category_context_async(
        self,
        category: str,
        card_ids: List[int],
        k: int = 3
    ) -> Dict[str, Any]:
        """
        Async version of retrieve_category_context for parallel execution
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.retrieve_category_context, category, card_ids, k)
        )

    async def retrieve_general_context_async(
        self,
        query: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Async version of retrieve_general_context for parallel execution
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.retrieve_general_context, query, k)
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics (Phase 3)
        
        Returns:
            Dictionary with cache performance metrics
        """
        if self.cache:
            return self.cache.get_stats()
        return {"cache_enabled": False}
    
    def clear_cache(self) -> int:
        """
        Clear all cached entries (Phase 3)
        
        Returns:
            Number of entries cleared
        """
        if self.cache:
            return self.cache.clear()
        return 0
