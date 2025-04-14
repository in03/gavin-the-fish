from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ..job_registry import job_registry

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

class JobStatusResponse(BaseModel):
    job_id: str
    tool_name: str
    status: str
    status_message: str
    created_at: str
    updated_at: str

class JobListResponse(BaseModel):
    jobs: List[JobStatusResponse]

@router.get("")
async def list_jobs() -> JobListResponse:
    """List all background jobs with their current status"""
    jobs = job_registry.get_all_jobs_with_status()
    return JobListResponse(jobs=jobs)

@router.get("/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status of a specific job"""
    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_info = {
        "job_id": job.job_id,
        "tool_name": job.tool_name,
        "status": job.status.value,
        "status_message": job.get_status_message(),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }
    return JobStatusResponse(**job_info)

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str) -> JobStatusResponse:
    """Cancel a running job"""
    success = job_registry.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or not cancelable")
        
    job = job_registry.get_job(job_id)
    job_info = {
        "job_id": job.job_id,
        "tool_name": job.tool_name,
        "status": job.status.value,
        "status_message": job.get_status_message(),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }
    return JobStatusResponse(**job_info)

@router.delete("/{job_id}")
async def delete_job(job_id: str) -> dict:
    """Delete a specific job by ID"""
    job = job_registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove the job from the registry
    del job_registry._jobs[job_id]
    return {"message": f"Job {job_id} deleted successfully"}

@router.delete("")
async def delete_all_jobs() -> dict:
    """Delete all jobs"""
    job_count = len(job_registry._jobs)
    job_registry._jobs.clear()
    return {"message": f"Deleted {job_count} jobs"} 