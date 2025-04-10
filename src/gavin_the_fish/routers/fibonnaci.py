from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from ..tool_logger import log_user_operation, OperationLogger
from ..job_registry import job_registry, JobStatus
from rich.console import Console
from typing import Optional

# Initialize console
console = Console()

router = APIRouter(
    prefix="/fibonacci",
    tags=["fibonacci"]
)

class FibonacciRequest(BaseModel):
    n: int
    owner: Optional[str] = None
    conversation_id: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number"""
    if n < 0:
        raise ValueError("Fibonacci sequence not defined for negative numbers")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

async def run_fibonacci_calculation(job_id: str, n: int, operation_logger: OperationLogger):
    """Background task to calculate Fibonacci number and update job status"""
    try:
        operation_logger.add_step(f"Starting Fibonacci calculation for n={n}")
        
        # Update job status to running
        job_registry.update_job(job_id, JobStatus.RUNNING)
        
        # Validate input
        if n > 1000:
            raise ValueError("Input too large - please use n <= 1000")
            
        # Calculate Fibonacci number
        result = calculate_fibonacci(n)
        
        operation_logger.add_step("Calculation completed successfully")
        
        # Update job with success and result
        job_registry.update_job(
            job_id,
            JobStatus.SUCCESS,
            result={
                "n": n,
                "result": result
            }
        )
        
    except ValueError as e:
        operation_logger.add_step(f"Validation error: {str(e)}")
        job_registry.update_job(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )
    except Exception as e:
        operation_logger.add_step(f"Unexpected error: {str(e)}")
        job_registry.update_job(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )

@router.post("/")
@log_user_operation("Calculate Fibonacci")
async def start_fibonacci_calculation(
    request: FibonacciRequest,
    background_tasks: BackgroundTasks,
    operation_logger: OperationLogger = None
) -> JobStatusResponse:
    """Start a Fibonacci calculation as a background job"""
    try:
        # Create a new job
        job = job_registry.create_job(
            tool_name="fibonacci",
            input={"n": request.n},
            owner=request.owner,
            conversation_id=request.conversation_id,
            cancelable=True
        )
        
        # Add the background task
        background_tasks.add_task(
            run_fibonacci_calculation,
            job.job_id,
            request.n,
            operation_logger
        )
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_fibonacci_status(job_id: str) -> JobStatusResponse:
    """Get the status of a Fibonacci calculation job"""
    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error
    )

@router.post("/cancel/{job_id}")
async def cancel_fibonacci_calculation(job_id: str) -> JobStatusResponse:
    """Cancel a running Fibonacci calculation job"""
    success = job_registry.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or not cancelable")
        
    job = job_registry.get_job(job_id)
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status
    )
