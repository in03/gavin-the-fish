from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess
from ..tool_logger import log_user_operation, OperationLogger
from ..job_registry import job_registry, JobStatus
from rich.console import Console
import asyncio
from typing import Optional

# Initialize console
console = Console()

router = APIRouter(
    prefix="/goose",
    tags=["goose"]
)

class GooseRequest(BaseModel):
    target: str
    owner: Optional[str] = None
    conversation_id: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

async def run_goose_command(job_id: str, target: str, operation_logger: OperationLogger):
    """Background task to run Goose command and update job status"""
    try:
        operation_logger.add_step(f"Starting Goose command for target: {target}")
        
        # Update job status to running
        job_registry.update_job(job_id, JobStatus.RUNNING)
        
        # Run the goose command
        process = subprocess.run(
            ["goose", "run", "-t", target],
            capture_output=True,
            text=True,
            check=True
        )
        
        operation_logger.add_step("Command completed successfully")
        
        # Update job with success and result
        job_registry.update_job(
            job_id,
            JobStatus.SUCCESS,
            result={
                "status": "success",
                "target": target,
                "output": process.stdout.strip()
            }
        )
        
    except subprocess.CalledProcessError as e:
        operation_logger.add_step(f"Command failed with exit code {e.returncode}")
        job_registry.update_job(
            job_id,
            JobStatus.FAILED,
            error=f"Command failed: {e.stderr.strip()}"
        )
    except Exception as e:
        operation_logger.add_step(f"Unexpected error: {str(e)}")
        job_registry.update_job(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )

@router.post("")
@log_user_operation("Run Goose MCP Command")
async def start_goose_command(
    request: GooseRequest,
    background_tasks: BackgroundTasks,
    operation_logger: OperationLogger = None
) -> JobStatusResponse:
    """Start a Goose MCP command as a background job"""
    try:
        # Create a new job
        job = job_registry.create_job(
            tool_name="goose",
            input={"target": request.target},
            owner=request.owner,
            conversation_id=request.conversation_id,
            cancelable=True
        )
        
        # Add the background task
        background_tasks.add_task(
            run_goose_command,
            job.job_id,
            request.target,
            operation_logger
        )
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_goose_status(job_id: str) -> JobStatusResponse:
    """Get the status of a Goose command job"""
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
async def cancel_goose_command(job_id: str) -> JobStatusResponse:
    """Cancel a running Goose command job"""
    success = job_registry.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or not cancelable")
        
    job = job_registry.get_job(job_id)
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status
    )

