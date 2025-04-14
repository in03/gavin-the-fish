"""
This router is used to start a timer for a specified duration.
The timer is a background task that will run for the specified duration and then send a message to the user.

Tool config:
{
  "name": "set_timer",
  "description": "Starts a countdown timer.",
  "parameters": {
    "type": "object",
    "properties": {
      "duration_seconds": {
        "type": "integer",
        "description": "The duration in seconds. For example, 300 for 5 minutes. If the user doesn't specify a duration, ask them how long they want the timer to run for."
      }
    },
    "required": ["duration_seconds"]
  }
}

"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..job_utils import job_router, JobRequest, JobResponse
from ..job_registry import JobStatus, job_registry
import asyncio

router = APIRouter(
    prefix="/timer",
    tags=["timer"]
)

class TimerRequest(JobRequest):
    duration_seconds: int

async def run_timer(job_id: str, duration_seconds: int):
    """Background task to run a timer"""
    try:
        # Update job status to running
        job_registry.update_job(job_id, JobStatus.RUNNING)
        
        # Validate input
        if duration_seconds <= 0:
            raise ValueError("Duration must be a positive number")
            
        # Wait for the specified duration
        await asyncio.sleep(duration_seconds)
        
        # Update job with success and result
        job_registry.update_job(
            job_id,
            JobStatus.SUCCESS,
            result={
                "duration_seconds": duration_seconds,
                "message": f"Timer completed after {duration_seconds} seconds"
            }
        )
        
    except Exception as e:
        job_registry.update_job(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )
        raise

@router.post("")
async def start_timer(request: TimerRequest, background_tasks: BackgroundTasks) -> JobResponse:
    """Start a timer as a background job"""
    try:
        # Create a new job
        job = job_registry.create_job(
            tool_name="timer",
            input=request.model_dump(),
            owner=request.owner,
            conversation_id=request.conversation_id,
            cancelable=True
        )
        
        # Add as a background task
        background_tasks.add_task(
            run_timer,
            job.job_id,
            request.duration_seconds
        )
        
        return JobResponse(
            job_id=job.job_id,
            status=job.status.value,
            result=job.result,
            error=job.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 