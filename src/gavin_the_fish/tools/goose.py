"""
Router for running Goose MCP commands.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from .decorator import tool, Parameter, JobSettings
from ..job_utils import JobResponse
from ..job_registry import job_registry, JobStatus
import subprocess
from rich.console import Console

# Initialize console
console = Console()

router = APIRouter(
    prefix="/goose",
    tags=["goose"]
)

@tool(
    name="goose",
    description="Run a Goose MCP command on a specified target.",
    settings=JobSettings(
        sync_threshold=5,
        job_timeout=0,
        notify_title="Goose Command Complete",
        notify_message="Goose command completed for target {target}",
        cancelable=True
    )
)
async def run_goose_command(
    job_id: str,
    target: str = Parameter(
        name="target",
        type="string",
        description="The target to run the Goose command on.",
        required=True
    )
) -> dict:
    """Run a Goose MCP command on the specified target"""
    try:
        # Run the goose command
        process = subprocess.run(
            ["goose", "run", "-t", target],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "target": target,
            "output": process.stdout.strip()
        }
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Command failed: {e.stderr.strip()}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")

@router.get("/status/{job_id}")
async def get_goose_status(job_id: str) -> JobResponse:
    """Get the status of a Goose command job"""
    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error
    )

