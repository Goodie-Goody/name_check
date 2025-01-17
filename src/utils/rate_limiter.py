"""
Rate limiting module.

This module provides functionality for applying rate limiting to requests.
"""

from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter

# Configure rate limiting settings
# Allow up to 50 requests per 60 seconds (1 minute) per client
limiter = RateLimiter(times=50, seconds=60)

async def rate_limit(request: Request, response: Response):
    """
    Apply rate limiting to requests.

    Args:
        request (Request): The incoming request object.
        response (Response): The outgoing response object.

    Returns:
        Response: The result of the rate limiter applied to the request and response.
    """
    # Apply the rate limiter to the request and response objects as middleware
    return await limiter(request, response)
