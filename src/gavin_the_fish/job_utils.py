from typing import Type, Optional, Dict, Any, Callable, TypeVar, ContextManager, AsyncContextManager
from pydantic import BaseModel
from fastapi import BackgroundTasks, HTTPException
from .job_registry import job_registry, JobStatus
from contextlib import asynccontextmanager
import inspect

T = TypeVar('T', bound=BaseModel)

class JobRequest(BaseModel):
    """Base class for job requests"""
    owner: Optional[str] = None
    conversation_id: Optional[str] = None

class JobResponse(BaseModel):
    """Base class for job responses"""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@asynccontextmanager
async def job_context(job_id: str) -> AsyncContextManager[None]:
    """
    Async context manager for handling job status updates.
    Automatically sets job to RUNNING on entry and handles errors.
    
    Example:
        ```python
        async with job_context(job_id):
            # Do work
            job_registry.update_job(job_id, JobStatus.SUCCESS, result={"data": "result"})
        ```
    """
    try:
        # Set job to running
        job_registry.update_job(job_id, JobStatus.RUNNING)
        yield
    except Exception as e:
        # Update job with error
        job_registry.update_job(
            job_id,
            JobStatus.FAILED,
            error=f"Job failed: {str(e)}"
        )
        raise

def job_router(
    tool_name: str,
    request_model: Type[BaseModel],
    cancelable: bool = False
) -> Callable[[Callable], Callable]:
    """
    Decorator to create a job router with standardized job creation and handling.
    
    Args:
        tool_name: The name of the tool
        request_model: The Pydantic model for the request
        cancelable: Whether the job can be cancelled
    """
    def decorator(job_function: Callable) -> Callable:
        async def wrapper(
            request: request_model,
            background_tasks: BackgroundTasks
        ) -> JobResponse:
            try:
                # Create a new job
                job = job_registry.create_job(
                    tool_name=tool_name,
                    input=request.dict(),
                    owner=getattr(request, 'owner', None),
                    conversation_id=getattr(request, 'conversation_id', None),
                    cancelable=cancelable
                )
                
                # Add as a background task
                background_tasks.add_task(
                    job_function,
                    job.job_id,
                    **{k: v for k, v in request.dict().items() if k not in ['owner', 'conversation_id']}
                )
                
                return JobResponse(
                    job_id=job.job_id,
                    status=job.status.value,
                    result=job.result,
                    error=job.error
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return wrapper
    return decorator

def update_job_status(
    job_id: str,
    status: JobStatus,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    """Update job status and related fields"""
    job_registry.update_job(job_id, status, result, error) 