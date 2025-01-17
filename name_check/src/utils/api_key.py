"""
API key validation module.

This module provides functionality for validating API keys for requests.
"""

import os

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = os.getenv("API_KEY_NAME")
api_key_header_def = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(header: str = Security(api_key_header_def)):
    """
    Validate the provided API key.

    Args:
        header (str): The API key provided in the request header.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException: If the API key is invalid.
    """
    if header == API_KEY:
        return header
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate API key"
        )
