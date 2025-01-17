"""
Scheduler utility module.

This module manages the setup, running, and shutdown of the job scheduler for
the Job Title Categorization API.
"""

import sys
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from services.service_data import initialize_service_types
from database import get_db, engine  # Import engine at the top level
from utils.logging_config import LoggerManager  # Import LoggerManager

# pylint: disable=invalid-name
logger = None  # This will be set up when the module is used

def setup_logger():
    """
    Set up the logger for this module.
    
    Note: This method should be called at the start of the application or wherever 
    the scheduler is initialized to ensure logging capabilities are set up.
    """
    global logger # pylint: disable=global-statement
    if logger is None:
        logger = LoggerManager.get_logger()  # Get the logger synchronously
    if logger is None:
        raise RuntimeError("Failed to set up logger in scheduler module")

def shutdown_scheduler(scheduler):
    """
    Safely shutdown the scheduler if it exists and is running.
    """
    if scheduler and getattr(scheduler, 'running', False):
        try:
            scheduler.shutdown(wait=False)
            if logger is not None:
                logger.info("Scheduler shutdown completed")
            else:
                print("Scheduler shutdown completed (logger not available)")
        except (RuntimeError, ValueError, ConnectionError) as e:
            if logger is not None:
                logger.error("Error during scheduler shutdown: %s", e)
            else:
                print(f"Error during scheduler shutdown: {e}")

async def shutdown_event_loop():
    """
    Gracefully shut down the event loop, tasks, and the database engine.
    """
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        for task in done:
            exception = task.exception()
            if exception:
                if logger is not None:
                    logger.error(f"Task {task.get_name()} raised exception: {exception}")
                else:
                    print(f"Task {task.get_name()} raised exception: {exception}")
    except asyncio.CancelledError:
        if logger is not None:
            logger.info("A task was canceled during shutdown, which is expected.")
        else:
            print("A task was canceled during shutdown, which is expected. Here's the context:")
            if hasattr(sys.exc_info()[1], '__context__'):
                print(sys.exc_info()[1].__context__)
    finally:
        # Close database connections
        await engine.dispose()
        if logger is not None:
            logger.info("All tasks have been cancelled or completed. Database connections closed.")
        else:
            print("All tasks have been cancelled or completed. Database connections closed.")

async def refresh_embeddings():
    """
    Refresh the service type embeddings.

    This function updates the service type embeddings using the model stored in app state.
    """
    async with (await get_db().__anext__()) as db:
        model = FastAPI().state.model  # This assumes the model is stored in app.state.
        await initialize_service_types(model, db)
        if logger is not None:
            logger.info("Service type embeddings have been refreshed.")
        else:
            print("Service type embeddings have been refreshed.")

def start_scheduler():
    """
    Start the APScheduler scheduler.

    This function adds a job to refresh the service type embeddings at a
    specified interval and starts the scheduler.

    Returns:
        AsyncIOScheduler: The started scheduler instance.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_embeddings,
        'interval',
        hours=12,
        id='refresh_embeddings',
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
