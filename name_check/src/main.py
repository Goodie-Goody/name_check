"""
Main module for initializing and running the Job Title Categorization API.

This module sets up logging, configures the FastAPI application, and runs the
server. It includes middleware, routers, and exception handlers.
"""

import time
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

from middleware.security_headers import SecurityHeadersMiddleware
from routers import categorize, health, root
from utils.logging_config import LoggerManager, get_shutdown_context
from utils.redis_config import configure_redis, redis_client
from utils.scheduler import start_scheduler, shutdown_scheduler, shutdown_event_loop
from database import initialize_db, get_db
from services.service_data import initialize_service_types

# Configure logging
logger = LoggerManager.get_logger() # pylint: disable=invalid-name


@asynccontextmanager
async def app_lifespan(application: FastAPI):
    """
    Context manager for application lifespan events.
    
    Initializes resources such as the database, model, service types, 
    Redis configuration, and scheduler during the application startup. 
    Handles cleanup and shutdown of these resources during application shutdown.
    
    Args:
        application (FastAPI): The FastAPI application instance.
    
    Yields:
        None: Allows the application to run after initialization is complete.
    
    Raises:
        RuntimeError, ValueError, OSError: Specific exceptions 
        that are caught during initialization.
    """
    logger.info("Starting application initialization...")
    try:
        # Initialize database
        logger.info("Initializing database...")
        start_time = time.time()
        await initialize_db()
        logger.info("Database initialized in %.2f seconds", time.time() - start_time)

        # Load model and store in app state
        logger.info("Loading model...")
        start_time = time.time()
        application.state.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded in %.2f seconds", time.time() - start_time)

        # Initialize service types
        logger.info("Initializing service types...")
        async with (await get_db().__anext__()) as db:
            await initialize_service_types(application.state.model, db)

        # Configure Redis
        logger.info("Configuring Redis...")
        await configure_redis()
        await FastAPILimiter.init(redis_client)

        # Start the scheduler
        logger.info("Starting scheduler...")
        application.state.scheduler = start_scheduler()

        # Application runs until shutdown is triggered
        yield

    except (RuntimeError, ValueError, OSError) as e:
        # Catch specific expected exceptions
        logger.error("Error during initialization: %s", e)
        raise
    except Exception as e:
        # Catch any unexpected exceptions
        logger.error("Unexpected error during initialization: %s", e)
        raise
    finally:
        with get_shutdown_context() as shutdown_logger:
            shutdown_logger.info("Starting application shutdown...")
        try:
            if hasattr(application.state, "scheduler") and application.state.scheduler.running:
                shutdown_scheduler(application.state.scheduler)
            await shutdown_event_loop()
        except asyncio.CancelledError:
            shutdown_logger.info("Task cancellation during shutdown (expected)")
            shutdown_logger.error(f"Error during shutdown: {e}")
        finally:
            shutdown_logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Job Title Categorization API",
    description="This API categorizes job titles using a sentence transformer model.",
    version="1.0.0",
    contact={
        "name": "Vmodel",
        "url": "https://www.vmodelapp.com/",
        "email": "goodkc12@gmail.com",
    },
    lifespan=app_lifespan,
)

# Include routers
app.include_router(categorize.router)
app.include_router(health.router)
app.include_router(root.router)

# Middleware configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to allow specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SecurityHeadersMiddleware)

@app.get("/", summary="Root Endpoint", description="Root endpoint returning a welcome message.")
async def read_root():
    """
    Root endpoint returning a welcome message and API version.

    Returns:
        dict: A dictionary containing the welcome message and API version.
    """
    return {
        "message": "Welcome to the Job Title Categorization API",
        "version": app.version,
        "documentation": {
            "Swagger UI": "/docs",
            "ReDoc": "/redoc",
        },
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """
    Handle HTTP exceptions.

    Args:
        _: The request object (unused).
        exc (HTTPException): The HTTP exception raised.

    Returns:
        JSONResponse: JSON response with the exception details.
    """
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError):
    """
    Handle ValueError exceptions.

    Args:
        _: The request object (unused).
        exc (ValueError): The exception raised.

    Returns:
        JSONResponse: JSON response with the exception details.
    """
    logger.error("ValueError caught: %s", exc)
    return JSONResponse(status_code=400, content={"message": f"ValueError: {exc}"})

@app.exception_handler(RuntimeError)
async def runtime_error_handler(_: Request, exc: RuntimeError):
    """
    Handle RuntimeError exceptions.

    Args:
        _: The request object (unused).
        exc (RuntimeError): The exception raised.

    Returns:
        JSONResponse: JSON response with the exception details.
    """
    logger.error("RuntimeError caught: %s", exc)
    return JSONResponse(status_code=500, content={"message": f"RuntimeError: {exc}"})

if __name__ == "__main__":
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=False)
