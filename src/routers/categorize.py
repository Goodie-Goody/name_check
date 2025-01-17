"""
Router for categorizing job titles.

This module provides endpoints for categorizing job titles into top matching service types.
"""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security.api_key import APIKey

from schemas.job_title import JobTitle
from services.service_data import get_top_service_types
from utils.redis_config import get_or_cache_embedding
from utils.api_key import get_api_key
from utils.rate_limiter import rate_limit

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/categorize",
    summary="Categorize a Job Title",
    description="Categorize a single title into top matching service types."
)
async def categorize_job_title(
    job_title: JobTitle,
    request: Request,
    _api_key: APIKey = Depends(get_api_key),
    _limit: None = Depends(rate_limit)
):
    """
    Categorize a single job title into top matching service types.

    Returns:
        dict: A result for the job title.
    """
    model = request.app.state.model

    # Ensure model is not None
    if model is None:
        logger.error("Model is not initialized")
        raise HTTPException(status_code=500, detail="Model is not initialized")

    # Validate the job title
    title = job_title.title
    if not re.match(r'^[a-zA-Z0-9\s\.,!?-]+$', title):
        logger.error("Invalid title: %s", title)
        raise HTTPException(status_code=400, detail="Invalid job title.")

    # Asynchronously get or cache embeddings with user_id in cache key
    cache_key = f"{job_title.user_id}:{title}"
    embedding = await get_or_cache_embedding(title, model, cache_key=cache_key)

    if embedding is None:
        raise HTTPException(status_code=500, detail="Failed to obtain embedding for the job title.")

    # Get top service types for the embedding (now returns list of strings only)
    categories = get_top_service_types([embedding], top_n=5)[0]

    # Prepare the response
    result = {
        "user_id": job_title.user_id,
        "title": title,
        "categories": categories  # A list of strings
    }

    return result
