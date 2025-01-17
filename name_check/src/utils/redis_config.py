"""
Redis configuration module.

This module provides functionality to configure Redis and manage cache embeddings.
"""

import os
import asyncio
import pickle
import logging
import redis.asyncio as redis
from fastapi import HTTPException
from redis.asyncio import ConnectionPool
from fastapi_limiter import FastAPILimiter
from dotenv import load_dotenv

# Load environment variables if necessary
load_dotenv()

# Initialize Redis connection pool
redis_pool = ConnectionPool(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    password=os.getenv('REDIS_PASSWORD', None),
    db=0
)

# Create an asyncio Redis client
redis_client = redis.Redis(connection_pool=redis_pool)

async def configure_redis():
    """
    Configure Redis settings and initialize FastAPILimiter.

    Sets the maximum memory usage and memory policy for Redis.

    Returns:
        None
    """
    try:
        await redis_client.execute_command('CONFIG SET maxmemory 256mb')
        await redis_client.execute_command('CONFIG SET maxmemory-policy volatile-lfu')
        await FastAPILimiter.init(redis_client)  # Initialize FastAPILimiter with Redis client
        logging.info("Redis configuration updated successfully")
    except redis.RedisError as e:
        logging.error("Failed to configure Redis: %s", e)

async def check_redis_connection():
    """
    Check the Redis connection status.

    Raises:
        HTTPException: If there is a Redis connection error.
    """
    try:
        await redis_client.ping()
        logging.info("Redis connection successful")
    except redis.RedisError as e:
        error_msg = (
            "Redis connection error: %s. Check if the Redis server is "
            "running and the connection details are correct."
        )
        logging.error(error_msg, e)
        raise HTTPException(status_code=500, detail=error_msg % e) from e

async def ensure_redis_connection():
    """
    Ensures that the Redis connection is established before performing any operations.
    This is crucial for caching embeddings or other Redis-based operations.

    Returns:
        None
    """
    try:
        # Attempt to ping Redis to check the connection
        await redis_client.ping()
        logging.info("Redis connection verified.")
    except redis.RedisError as e:
        error_msg = (
            "Failed to establish Redis connection: %s. Please check the Redis server."
        )
        logging.error(error_msg, e)
        raise HTTPException(status_code=500, detail=error_msg % e) from e

async def get_or_cache_embedding(key: str, model, cache_key: str = None, ttl: int = 3600):
    """
    Retrieve or cache the embedding for a given key.

    Args:
        key (str): The key to encode.
        model: The model used to generate embeddings.
        cache_key (str, optional): The cache key for the embedding. Defaults to None.
        ttl (int, optional): Time-to-live for the cache in seconds. Defaults to 3600.

    Returns:
        The embedding for the given key.

    Raises:
        ValueError: If the TTL is not a positive integer.
        HTTPException: If there's an error with Redis or model computation.
    """
    if cache_key is None:
        cache_key = key

    if not isinstance(ttl, int) or ttl <= 0:
        raise ValueError("TTL must be a positive integer")

    # Ensure Redis connection before continuing
    await ensure_redis_connection()

    cache_key = str(cache_key)
    cached_embedding = await redis_client.get(cache_key)
    if cached_embedding:
        return pickle.loads(cached_embedding)
    lock_key = f"lock:{cache_key}"
    async with redis_client.lock(lock_key, timeout=10):
        cached_embedding = await redis_client.get(cache_key)
        if cached_embedding:
            return pickle.loads(cached_embedding)

        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, model.encode, key)
            await redis_client.setex(cache_key, ttl, pickle.dumps(embedding))
        except Exception as e:
            logging.error("Failed to compute or cache embedding: %s", e)
            raise HTTPException(status_code=500, detail="Failed to process embedding") from e

    return embedding
