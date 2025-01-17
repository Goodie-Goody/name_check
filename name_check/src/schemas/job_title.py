"""
Schema for job title inputs.

This module defines the Pydantic model for validating job title inputs.
"""

from pydantic import BaseModel, Field

class JobTitle(BaseModel):
    """Model for a single job title input, including user ID."""
    user_id: int = Field(
        ...,
        description="Unique identifier for the user making the request."
    )
    title: str = Field(
        ...,
        description="A single job title to be categorized."
    )
