from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any, Callable, List
import uuid
from dataclasses import dataclass, field
from .tool_logger import OperationLogger

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

@dataclass
class Job:
    """Represents a background job in the system."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: Optional[str] = None
    cancelable: bool = True
    tags: List[str] = field(default_factory=list)
    conversation_id: Optional[str] = None
    llm_context_id: Optional[str] = None
    
    # Lifecycle hooks
    on_cancel: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_fail: Optional[Callable] = None
    
    def update_status(self, new_status: JobStatus, result: Any = None, error: str = None):
        """Update job status and trigger appropriate lifecycle hooks."""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if result is not None:
            self.result = result
        if error is not None:
            self.error = error
            
        # Trigger lifecycle hooks
        if new_status == JobStatus.SUCCESS and self.on_complete:
            self.on_complete(self)
        elif new_status == JobStatus.FAILED and self.on_fail:
            self.on_fail(self)
        elif new_status == JobStatus.CANCELLED and self.on_cancel:
            self.on_cancel(self)
    
    def get_status_message(self) -> str:
        """Generate a human-readable status message for the job."""
        if self.status == JobStatus.PENDING:
            return f"Waiting to start {self.tool_name} job"
        elif self.status == JobStatus.RUNNING:
            return f"Currently running {self.tool_name} job"
        elif self.status == JobStatus.SUCCESS:
            if self.tool_name == "fibonacci":
                return f"Fibonacci calculation completed. The result is {self.result['result']}"
            elif self.tool_name == "goose":
                return f"Goose command completed successfully for target {self.result['target']}"
            else:
                return f"{self.tool_name} job completed successfully"
        elif self.status == JobStatus.FAILED:
            return f"Job failed: {self.error}"
        elif self.status == JobStatus.CANCELLED:
            return f"Job was cancelled"
        elif self.status == JobStatus.EXPIRED:
            return f"Job has expired"
        return f"Unknown status for {self.tool_name} job"

class JobRegistry:
    """In-memory job registry for managing background jobs."""
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._logger = OperationLogger("JobRegistry", quick=True)
    
    def create_job(
        self,
        tool_name: str,
        input: Dict[str, Any],
        owner: Optional[str] = None,
        cancelable: bool = True,
        tags: List[str] = None,
        conversation_id: Optional[str] = None,
        llm_context_id: Optional[str] = None,
        on_cancel: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_fail: Optional[Callable] = None
    ) -> Job:
        """Create a new job and add it to the registry."""
        job = Job(
            tool_name=tool_name,
            input=input,
            owner=owner,
            cancelable=cancelable,
            tags=tags or [],
            conversation_id=conversation_id,
            llm_context_id=llm_context_id,
            on_cancel=on_cancel,
            on_complete=on_complete,
            on_fail=on_fail
        )
        
        self._jobs[job.job_id] = job
        self._logger.add_step(f"Created job {job.job_id} for tool {tool_name}")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by its ID."""
        return self._jobs.get(job_id)
    
    def update_job(
        self,
        job_id: str,
        status: JobStatus,
        result: Any = None,
        error: str = None
    ) -> bool:
        """Update a job's status and trigger lifecycle hooks."""
        job = self.get_job(job_id)
        if not job:
            return False
            
        job.update_status(status, result, error)
        self._logger.add_step(f"Updated job {job_id} to status {status}")
        return True
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it's cancelable."""
        job = self.get_job(job_id)
        if not job or not job.cancelable:
            return False
            
        return self.update_job(job_id, JobStatus.CANCELLED)
    
    def list_jobs(
        self,
        owner: Optional[str] = None,
        status: Optional[JobStatus] = None,
        tool_name: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> List[Job]:
        """List jobs matching the given filters."""
        jobs = self._jobs.values()
        
        if owner:
            jobs = [j for j in jobs if j.owner == owner]
        if status:
            jobs = [j for j in jobs if j.status == status]
        if tool_name:
            jobs = [j for j in jobs if j.tool_name == tool_name]
        if conversation_id:
            jobs = [j for j in jobs if j.conversation_id == conversation_id]
            
        return list(jobs)
    
    def get_all_jobs_with_status(self) -> List[Dict[str, Any]]:
        """Get all jobs with their human-readable status messages."""
        return [
            {
                "job_id": job.job_id,
                "tool_name": job.tool_name,
                "status": job.status,
                "status_message": job.get_status_message(),
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }
            for job in self._jobs.values()
        ]
    
    def cleanup_expired_jobs(self, max_age_seconds: int = 3600) -> int:
        """Remove jobs older than max_age_seconds."""
        now = datetime.now()
        expired_jobs = [
            job_id for job_id, job in self._jobs.items()
            if (now - job.created_at).total_seconds() > max_age_seconds
        ]
        
        for job_id in expired_jobs:
            self._jobs.pop(job_id)
            
        return len(expired_jobs)

# Global job registry instance
job_registry = JobRegistry() 