"""
Vector Store for RAG System using ChromaDB

This module provides vector storage and similarity search capabilities
for the Tarot reading application's knowledge base.

Classes:
    VectorStore: ChromaDB-based vector database for semantic search
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb

from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector store using ChromaDB for semantic similarity search

    This class manages a persistent ChromaDB collection for storing
    and retrieving Tarot knowledge base documents.

    Attributes:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory for ChromaDB persistence
        client: ChromaDB client instance
        collection: ChromaDB collection instance
    """

    def __init__(
        self,
        collection_name: str = "tarot_knowledge",
        persist_directory: Optional[str] = None
    ):
        """
        Initialize the vector store

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for data persistence (default: backend/data/embeddings/chroma_db)
        """
        self.collection_name = collection_name

        # Set default persist directory
        if persist_directory is None:
            backend_root = Path(__file__).parent.parent.parent.parent
            persist_directory = str(backend_root / "data" / "embeddings" / "chroma_db")

        self.persist_directory = persist_directory

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client (using persistent client for data storage)
        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        # Initialize collection
        self.collection = None
        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """Initialize or get existing ChromaDB collection"""
        try:
            # Get embedding model for dimension
            embedding_model = get_embedding_model()
            embedding_dim = embedding_model.get_embedding_dimension()

            logger.info(f"Initializing ChromaDB collection: {self.collection_name}")
            logger.info(f"Persist directory: {self.persist_directory}")
            logger.info(f"Embedding dimension: {embedding_dim}")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"embedding_dimension": embedding_dim}
            )

            logger.info(f"Collection initialized. Document count: {self.collection.count()}")

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """
        Add documents to the vector store

        Args:
            documents: List of text documents to add
            metadatas: List of metadata dictionaries for each document
            ids: List of unique IDs for each document

        Raises:
            ValueError: If lists have different lengths
        """
        if not (len(documents) == len(metadatas) == len(ids)):
            raise ValueError("documents, metadatas, and ids must have the same length")

        if not documents:
            logger.warning("No documents to add")
            return

        try:
            # Get embeddings
            embedding_model = get_embedding_model()
            embeddings = embedding_model.encode(documents)

            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents

        Args:
            query: Query text
            k: Number of results to return
            filter_dict: Optional metadata filter

        Returns:
            Dictionary containing:
                - documents: List of matching document texts
                - metadatas: List of metadata for each document
                - distances: List of similarity distances
                - ids: List of document IDs

        Raises:
            ValueError: If k is less than 1
        """
        if k < 1:
            raise ValueError("k must be at least 1")

        try:
            # Get query embedding
            embedding_model = get_embedding_model()
            query_embedding = embedding_model.encode_single(query)

            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=filter_dict
            )

            logger.debug(f"Search query: '{query}' | Results: {len(results['ids'][0])}")

            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID

        Args:
            doc_id: Document ID to retrieve

        Returns:
            Dictionary with document, metadata, and id, or None if not found
        """
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )

            if not results["ids"]:
                logger.warning(f"Document not found: {doc_id}")
                return None

            return {
                "id": results["ids"][0],
                "document": results["documents"][0],
                "metadata": results["metadatas"][0]
            }

        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            raise

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs

        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        try:
            # Delete and recreate collection
            self.client.delete_collection(name=self.collection_name)
            self._initialize_collection()
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_count(self) -> int:
        """
        Get the total number of documents in the collection

        Returns:
            Number of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get count: {e}")
            return 0
