from enum import Enum
from datetime import datetime
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass, field, asdict
import random
import string
from collections import defaultdict

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
    job_id: str
    tool_name: str
    input: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    owner: Optional[str] = None
    conversation_id: Optional[str] = None
    cancelable: bool = False
    on_status_change: Optional[Callable[['Job'], None]] = None
    context: Optional[Dict[str, Any]] = None

    def update(self, status: JobStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update job status and related fields"""
        self.status = status
        self.result = result
        self.error = error
        self.updated_at = datetime.now()
        
        if self.on_status_change:
            self.on_status_change(self)

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
            return "Job was cancelled"
        return f"Unknown status for {self.tool_name} job"

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for Redis storage"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary from Redis storage"""
        data['status'] = JobStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

class JobRegistry:
    """Registry to manage background jobs"""
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._status_change_callbacks: Dict[str, List[Callable[[Job], None]]] = {}

    def _generate_job_id(self) -> str:
        """Generate a unique job ID using 5 random lowercase alphanumeric characters"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

    def create_job(
        self,
        tool_name: str,
        input: Dict[str, Any],
        owner: Optional[str] = None,
        conversation_id: Optional[str] = None,
        cancelable: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Create a new job"""
        job_id = self._generate_job_id()
        job = Job(
            job_id=job_id,
            tool_name=tool_name,
            input=input,
            owner=owner,
            conversation_id=conversation_id,
            cancelable=cancelable,
            context=context
        )
        self._jobs[job_id] = job
        print(f"Created job {job_id} for tool {tool_name}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, status: JobStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update job status and related fields"""
        job = self.get_job(job_id)
        if job:
            job.update(status, result, error)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        if job and job.cancelable and job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            self.update_job(job_id, JobStatus.CANCELLED)
            return True
        return False

    def list_jobs(self) -> List[Job]:
        """List all jobs"""
        return list(self._jobs.values())

    def get_all_jobs_with_status(self) -> List[Dict[str, Any]]:
        """Get all jobs with their status information"""
        return [{
            "job_id": job.job_id,
            "tool_name": job.tool_name,
            "status": job.status.value,
            "status_message": job.get_status_message(),
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        } for job in self._jobs.values()]

job_registry = JobRegistry() 