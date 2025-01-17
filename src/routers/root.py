from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Root Endpoint", description="Root endpoint returning a welcome message.")
async def read_root():
    """
    Root endpoint returning a welcome message and API version.

    Returns:
        dict: A dictionary containing the welcome message and API version.
    """
    return {
        "message": "Welcome to the Job Title Categorization API",
        "version": "1.0.0",  # You might want to dynamically pull this from the app
        "documentation": {
            "Swagger UI": "/docs",
            "ReDoc": "/redoc"
        }
    }
