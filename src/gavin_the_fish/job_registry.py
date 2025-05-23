from enum import Enum
from datetime import datetime
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass, field, asdict
import random
import string
from collections import defaultdict
import rumps

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
    notify_on_completion: bool = False
    notification_title: Optional[str] = None
    notification_message: Optional[str] = None

    def update(self, status: JobStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update job status and related fields"""
        self.status = status
        self.result = result
        self.error = error
        self.updated_at = datetime.now()

        if self.on_status_change:
            self.on_status_change(self)

        # Send notification if job is complete and notifications are enabled
        if self.notify_on_completion and status in [JobStatus.SUCCESS, JobStatus.FAILED]:
            self._send_notification()

    def _format_with_context(self, template_str):
        """Format a string with combined context from input and result"""
        if not template_str or '{' not in template_str or '}' not in template_str:
            return template_str

        # Create a combined context from input and result
        context = {}
        if self.input:
            context.update(self.input)
        if self.result:
            context.update(self.result)

        try:
            return template_str.format(**context)
        except KeyError:
            # Fallback: replace only the keys that exist
            import re
            pattern = r'\{([^{}]+)\}'

            def replace_if_exists(match):
                key = match.group(1)
                return str(context[key]) if key in context else f"{{{key}}}"

            return re.sub(pattern, replace_if_exists, template_str)
        except Exception as e:
            print(f"Warning: Error formatting message: {e}")
            return template_str

    def _send_notification(self):
        """Send a native notification for job completion"""
        try:
            title = self.notification_title or f"{self.tool_name} job completed"
            message_template = self.notification_message or self.get_status_message()

            # Format the message with the combined context
            message = self._format_with_context(message_template)

            rumps.notification(title, subtitle="Gavin the Fish", message=message)
        except Exception as e:
            print(f"Failed to send notification: {e}")

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
        context: Optional[Dict[str, Any]] = None,
        notify_on_completion: bool = False,
        notification_title: Optional[str] = None,
        notification_message: Optional[str] = None
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
            context=context,
            notify_on_completion=notify_on_completion,
            notification_title=notification_title,
            notification_message=notification_message
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