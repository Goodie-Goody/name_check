"""
Health check router module.

This module provides a health 
check endpoint for monitoring 
the status of the Job Title
Categorization API.
"""

from fastapi import APIRouter, status

router = APIRouter()

@router.get(
    "/health",
    summary="Health Check",
    description="Endpoint to check the health status of the API.",
    status_code=status.HTTP_200_OK
)
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: A message indicating the API is healthy.
    """
    return {"status": "healthy"}
