"""
Timer tool for setting countdown timers.

This tool allows setting a timer for a specified duration and notifies when complete.
"""

import asyncio
import logging
from typing import Dict, Any
from .core import tool, Parameter, JobSettings
from rich.console import Console

# Initialize console
console = Console()

logger = logging.getLogger(__name__)

@tool(
    name="timer",
    description="Set a countdown timer for a specified duration",
    parameters=[
        Parameter(
            name="duration_seconds",
            type="integer",
            description="The duration in seconds. For example, 300 for 5 minutes.",
            required=True
        ),
        Parameter(
            name="message",
            type="string",
            description="Optional message to provide user when the timer completes",
            required=False
        )
    ],
    settings=JobSettings(
        sync_threshold=3,  # Set to 3 seconds to match the example case
        job_timeout=0,
        notify_title="Timer Complete",
        notify_message="Timer for {duration_seconds} seconds has completed",
        cancelable=True
    )
)
async def set_timer(duration_seconds: int, message: str = None) -> Dict[str, Any]:
    """Set a timer for the specified duration."""
    try:
        # Wait for the duration
        await asyncio.sleep(duration_seconds)

        return {
            "status": "completed",
            "duration": duration_seconds,
            "message": message or f"Timer for {duration_seconds} seconds has completed"
        }
    except Exception as e:
        logger.error(f"Error in timer: {str(e)}")
        raise ValueError(f"Failed to set timer: {str(e)}")