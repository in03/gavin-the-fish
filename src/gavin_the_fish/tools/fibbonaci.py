"""
Router for calculating Fibonacci numbers.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from .decorator import tool, Parameter, JobSettings
from ..job_utils import JobResponse
from ..job_registry import job_registry, JobStatus
from rich.console import Console

# Initialize console
console = Console()

router = APIRouter(
    prefix="/fibonacci",
    tags=["fibonacci"]
)

def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number"""
    if n <= 0:
        raise ValueError("Input must be a positive integer")
    elif n == 1 or n == 2:
        return 1
    else:
        a, b = 1, 1
        for _ in range(3, n + 1):
            a, b = b, a + b
        return b

@tool(
    name="fibonacci",
    description="Calculate the nth Fibonacci number.",
    settings=JobSettings(
        sync_threshold=5,
        job_timeout=0,
        notify_title="Fibonacci Calculation Complete",
        notify_message="Fibonacci calculation completed for n={n}",
        cancelable=True
    )
)
async def run_fibonacci_calculation(
    job_id: str,
    n: int = Parameter(
        name="n",
        type="integer",
        description="The position in the Fibonacci sequence to calculate (must be > 0 and <= 1000).",
        required=True
    )
) -> dict:
    """Calculate the nth Fibonacci number"""
    # Validate input
    if n > 1000:
        raise ValueError("Input too large - please use n <= 1000")
        
    # Calculate Fibonacci number
    result = calculate_fibonacci(n)
    
    return {
        "n": n,
        "result": result
    }

@router.get("/status/{job_id}")
async def get_fibonacci_status(job_id: str) -> JobResponse:
    """Get the status of a Fibonacci calculation job"""
    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error
    )
