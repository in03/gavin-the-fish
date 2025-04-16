"""
This router is used to start a timer for a specified duration.
The timer is a background task that will run for the specified duration and then send a message to the user.

Tool config:
{
  "name": "set_timer",
  "description": "Starts a countdown timer for a specified duration. The timer will run in the background and notify when complete.",
  "parameters": {
    "type": "object",
    "properties": {
      "duration_seconds": {
        "type": "integer",
        "description": "The duration in seconds. For example, 300 for 5 minutes. If the user doesn't specify a duration, ask them how long they want the timer to run for."
      },
    },
    "required": ["duration_seconds"]
  }
}

"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from .decorator import tool, Parameter, JobSettings
import asyncio
import uuid

router = APIRouter(
    prefix="/timer",
    tags=["timer"]
)

@tool(
    name="set_timer",
    description="Starts a countdown timer for a specified duration. The timer will run in the background and notify when complete.",
    settings=JobSettings(
        sync_threshold=5,
        job_timeout=0,
        notify_title="Timer Complete",
        notify_message="Timer completed after {duration_seconds} seconds",
        cancelable=True
    )
)
async def run_timer(
    job_id: str,
    duration_seconds: int = Parameter(
        description="The duration in seconds. For example, 300 for 5 minutes. If the user doesn't specify a duration, ask them how long they want the timer to run for.",
        required=True
    ),
    notify_on_completion: bool = Parameter(
        description="Whether to show a notification when the timer completes.",
        required=False,
        default=False
    )
) -> dict:
    """Start a timer for the specified duration."""
    try:
        # Start the timer in the background
        await asyncio.sleep(duration_seconds)
        
        # Return success response
        return {
            "status": "completed",
            "duration_seconds": duration_seconds,
            "notified": notify_on_completion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_timer(
    duration_seconds: int,
    notify_on_completion: bool = False
) -> dict:
    """Start a timer endpoint."""
    job_id = str(uuid.uuid4())
    return await run_timer(job_id, duration_seconds, notify_on_completion)

@router.get("/status/{job_id}")
async def get_timer_status(job_id: str) -> dict:
    """Get timer status endpoint."""
    return {"status": "running", "job_id": job_id} 