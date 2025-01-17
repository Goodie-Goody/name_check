"""
Service data management module with optimized logging.

This module defines the ServiceData class and associated functions for managing
service types and their embeddings for job title categorization.
"""

from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import numpy as np

from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_service_types
from utils.redis_config import get_or_cache_embedding, ensure_redis_connection
from utils.logging_config import get_logger

logger = get_logger("services.service_data")  # pylint: disable=invalid-name


class ServiceData:
    """
    Manages service types and their embeddings for categorization.
    """

    def __init__(self):
        self.categories: Dict[str, str] = {}
        self.category_embeddings: Dict[str, np.ndarray] = {}
        self.model: Optional[SentenceTransformer] = None
        self._service_types_list: List[str] = []
        self._category_embeddings_matrix: np.ndarray = np.array([])

    def update_embeddings(self):
        """
        Update internal NumPy arrays for vectorized computations.

        Raises:
            ValueError: If no category embeddings are available to update.
        """
        if not self.category_embeddings:
            raise ValueError("No category embeddings available to update.")
        self._service_types_list = list(self.category_embeddings.keys())
        self._category_embeddings_matrix = np.array(
            list(self.category_embeddings.values())
        )

    @property
    def service_types_list(self) -> List[str]:
        """Get the list of service type names."""
        return self._service_types_list

    @property
    def category_embeddings_matrix(self) -> np.ndarray:
        """Get the NumPy array of category embeddings."""
        return self._category_embeddings_matrix


service_data = ServiceData()


@asynccontextmanager
async def redis_session():
    """
    Context manager for Redis operations that ensures connection is established once.
    """
    await ensure_redis_connection()
    try:
        yield
    finally:
        pass  # Connection handling is managed by the Redis client


async def initialize_service_types(model: SentenceTransformer, db: AsyncSession, ttl: int = 14400):
    """
    Initialize service types and their embeddings asynchronously.

    Args:
        model (SentenceTransformer): The sentence transformer model used for embeddings.
        db (AsyncSession): The asynchronous database session.
        ttl (int): Time-to-live for cached embeddings in seconds, default is 14400 (4 hours).

    Raises:
        ValueError: If TTL is not a positive integer.
        Exception: If there's an error during initialization.
    """
    try:
        logger.info("Starting initialization of service types.")

        if not isinstance(ttl, int) or ttl <= 0:
            raise ValueError("TTL must be a positive integer.")

        service_data.model = model

        logger.info("Fetching service types from the database.")
        service_types_data = await get_service_types(db)
        logger.info("Fetched %d service types.", len(service_types_data))
        service_data.categories.clear()
        service_data.category_embeddings.clear()

        # Use a single Redis connection for all operations
        async with redis_session():
            for service_type in service_types_data:
                service_data.categories[service_type.name] = service_type.name
                embedding_key = f"category:{service_type.name}"
                # Process each service type
                logger.debug("Processing service type: %s", service_type.name)
                embedding = await get_or_cache_embedding(
                    service_type.name, model, cache_key=embedding_key, ttl=ttl
                )
                service_data.category_embeddings[service_type.name] = embedding

        logger.info("Updating internal embeddings.")
        service_data.update_embeddings()

        logger.info("Service types and embeddings have been initialized successfully.")
    except Exception as exc:
        logger.error("Error during initialization at line %d: %s",
                    exc.__traceback__.tb_lineno, str(exc))
        raise


def get_top_service_types(embeddings: List[np.ndarray], top_n: int = 5) -> List[List[str]]:
    """
    Get top matching service types for a list of embeddings using cosine similarity.

    Args:
        embeddings (List[np.ndarray]): List of embeddings to find matches for.
        top_n (int, optional): Number of top matches to return. Defaults to 5.

    Returns:
        List[List[str]]: For each input embedding, returns a list of service type names.

    Raises:
        ValueError: If service types are not initialized or embeddings are invalid.
    """
    try:
        if not service_data.category_embeddings_matrix.size:
            raise ValueError("Service types not initialized. Run initialize_service_types first.")

        if not embeddings:
            raise ValueError("No embeddings provided.")

        # Convert input embeddings to numpy array
        embeddings_array = np.array(embeddings)
        # Compute cosine similarity between input embeddings and all category embeddings
        norm_categories = service_data.category_embeddings_matrix / np.linalg.norm(
            service_data.category_embeddings_matrix, axis=1, keepdims=True
        )
        norm_embeddings = embeddings_array / np.linalg.norm(
            embeddings_array, axis=1, keepdims=True
        )
        similarity_matrix = np.dot(norm_embeddings, norm_categories.T)

        # Get top N matches for each input embedding
        results = []
        for similarities in similarity_matrix:
            # Get indices of top N similarities
            top_indices = np.argsort(similarities)[-top_n:][::-1]
            # Create list of service type names only (without scores)
            matches = [service_data.service_types_list[idx] for idx in top_indices]
            results.append(matches)

        return results

    except Exception as exc:
        logger.error("Error in get_top_service_types: %s", str(exc))
        raise
