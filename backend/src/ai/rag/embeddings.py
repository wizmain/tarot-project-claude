"""
Embedding Model for RAG System

This module provides a singleton embedding model using sentence-transformers
for multilingual support (Korean/English) in the Tarot reading application.

Classes:
    EmbeddingModel: Singleton wrapper for sentence-transformers model
"""
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Singleton embedding model using sentence-transformers

    Uses 'paraphrase-multilingual-MiniLM-L12-v2' for Korean/English support.
    This model provides 384-dimensional embeddings suitable for semantic search.

    Attributes:
        model_name: Name of the sentence-transformers model
        model: The loaded SentenceTransformer instance
    """

    _instance: Optional['EmbeddingModel'] = None

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Initialize the embedding model

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the sentence-transformers model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully. Embedding dimension: {self.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts into embeddings

        Args:
            texts: List of text strings to encode

        Returns:
            numpy array of shape (len(texts), embedding_dim)

        Raises:
            ValueError: If model is not loaded or texts is empty
        """
        if not self.model:
            raise ValueError("Embedding model not loaded")

        if not texts:
            raise ValueError("texts cannot be empty")

        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            logger.debug(f"Encoded {len(texts)} texts into embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single text into an embedding

        Args:
            text: Text string to encode

        Returns:
            numpy array of shape (embedding_dim,)

        Raises:
            ValueError: If model is not loaded or text is empty
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        embeddings = self.encode([text])
        return embeddings[0]

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings

        Returns:
            Embedding dimension size
        """
        if not self.model:
            raise ValueError("Embedding model not loaded")

        return self.model.get_sentence_embedding_dimension()


# Singleton instance holder
_embedding_model_instance: Optional[EmbeddingModel] = None


def get_embedding_model(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> EmbeddingModel:
    """
    Get or create the singleton embedding model instance

    Args:
        model_name: Name of the sentence-transformers model (default: multilingual MiniLM)

    Returns:
        Singleton EmbeddingModel instance

    Usage:
        >>> embedding_model = get_embedding_model()
        >>> embeddings = embedding_model.encode(["Hello world", "Greetings"])
    """
    global _embedding_model_instance

    if _embedding_model_instance is None:
        logger.info("Creating new EmbeddingModel singleton instance")
        _embedding_model_instance = EmbeddingModel(model_name=model_name)

    return _embedding_model_instance
