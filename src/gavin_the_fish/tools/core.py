"""
Core tool definitions and types for the Gavin the Fish system.

This module provides the core functionality for defining and registering tools
that can be used by the ElevenLabs agent.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
import inspect
import logging
import asyncio
from ..job_utils import JobResponse, job_context
from ..job_registry import job_registry, JobStatus, Job

logger = logging.getLogger(__name__)

class Parameter(BaseModel):
    """Defines a parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None

class ToolSchema(BaseModel):
    """Defines the schema for a tool."""
    name: str
    description: str
    parameters: List[Parameter]

class JobSettings(BaseModel):
    """Defines settings for job execution."""
    sync_threshold: Optional[int] = None
    job_timeout: Optional[int] = None
    notify_title: Optional[str] = None
    notify_message: Optional[str] = None
    cancelable: bool = False

class ToolResult(BaseModel):
    """Standardized result format for tool execution"""
    job_id: Optional[str] = None
    tool_name: str
    status: str
    result: Dict[str, Any]
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    parameters: Dict[str, Any]
    status_message: Optional[str] = None
    is_job: bool = False

class ToolRegistry:
    """Registry for managing tools."""
    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._implementations: Dict[str, Callable] = {}
        self._job_settings: Dict[str, JobSettings] = {}
        self._routers: Dict[str, APIRouter] = {}

    def register(self, schema: ToolSchema, implementation: Callable, settings: Optional[JobSettings] = None) -> None:
        """Register a tool with its schema and implementation."""
        self._tools[schema.name] = schema
        self._implementations[schema.name] = implementation
        if settings:
            self._job_settings[schema.name] = settings

        # Create and register the router
        router = APIRouter(prefix=f"/{schema.name}", tags=[schema.name])

        # Add the main endpoint - handle both with and without trailing slash
        @router.post("")
        @router.post("/")
        async def execute_tool(request: Request, background_tasks: BackgroundTasks):
            try:
                # Get the request body
                body = await request.json()

                # Create a job for this execution
                job = job_registry.create_job(
                    tool_name=schema.name,
                    input=body,
                    cancelable=settings.cancelable if settings else False,
                    notify_on_completion=True if settings and (settings.notify_title or settings.notify_message) else False,
                    notification_title=settings.notify_title if settings else None,
                    notification_message=settings.notify_message if settings else None
                )

                # Filter out job-related parameters
                implementation_params = {
                    k: v for k, v in body.items()
                    if k not in ['notify_on_completion', 'notification_title', 'notification_message']
                }

                # If we have sync_threshold settings, handle accordingly
                if settings and settings.sync_threshold is not None:
                    # If sync_threshold is -1, block until complete
                    if settings.sync_threshold == -1:
                        # Run the job and wait for it
                        async with job_context(job.job_id):
                            result = await implementation(**implementation_params)

                            # Standardize the result
                            standardized_result = self._standardize_result(
                                job_id=job.job_id,
                                tool_name=schema.name,
                                status=JobStatus.SUCCESS.value,
                                result=result,
                                parameters=body,
                                is_job=True
                            )

                            # Update job status
                            job_registry.update_job(job.job_id, JobStatus.SUCCESS, result=standardized_result)

                            # Return the enriched result
                            return standardized_result

                    # If sync_threshold is falsey (0, False, None), return pending immediately
                    elif not settings.sync_threshold:
                        # Schedule the job in the background
                        background_tasks.add_task(self._run_job_in_background, job.job_id, implementation, implementation_params)

                        # Return pending status with rich context
                        return self._standardize_result(
                            job_id=job.job_id,
                            tool_name=schema.name,
                            status=JobStatus.PENDING.value,
                            result={},
                            parameters=body,
                            is_job=True
                        )

                    # For positive sync_threshold, handle based on job duration vs threshold
                    else:
                        try:
                            # Always start the job in the background immediately
                            # This ensures jobs run asynchronously regardless of sync_threshold
                            asyncio.create_task(self._run_job_in_background(job.job_id, implementation, implementation_params))

                            # Set job to running immediately
                            job_registry.update_job(job.job_id, JobStatus.RUNNING)

                            # For all other cases, wait up to sync_threshold
                            start_time = asyncio.get_event_loop().time()
                            while True:
                                # Check if job has completed
                                current_job = job_registry.get_job(job.job_id)
                                if current_job.status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
                                    # Job completed within sync threshold, return the result immediately
                                    return self._standardize_result(
                                        job_id=job.job_id,
                                        tool_name=schema.name,
                                        status=current_job.status.value,
                                        result=current_job.result or {},
                                        error=current_job.error,
                                        parameters=body,
                                        is_job=True,
                                        started_at=current_job.created_at.isoformat(),
                                        completed_at=current_job.updated_at.isoformat(),
                                        status_message=current_job.get_status_message() if hasattr(current_job, 'get_status_message') else None
                                    )

                                # Check if we've waited long enough
                                elapsed = asyncio.get_event_loop().time() - start_time
                                if elapsed >= settings.sync_threshold:
                                    # Sync threshold reached, return pending status
                                    return self._standardize_result(
                                        job_id=job.job_id,
                                        tool_name=schema.name,
                                        status=JobStatus.PENDING.value,
                                        result={},
                                        parameters=body,
                                        is_job=True,
                                        started_at=job.created_at.isoformat()
                                    )

                                # Wait a bit before checking again
                                await asyncio.sleep(0.1)

                        except Exception as e:
                            # If there's an error, update the job and re-raise
                            job_registry.update_job(job.job_id, JobStatus.FAILED, error=str(e))
                            raise

                # If no job settings, run synchronously
                else:
                    result = await implementation(**implementation_params)

                    # Return simple standardized result for non-job tools
                    return self._standardize_result(
                        tool_name=schema.name,
                        status="success",
                        result=result,
                        parameters=body,
                        is_job=False
                    )

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Add the status endpoint if it's a job - handle both with and without trailing slash
        if settings and (settings.job_timeout is not None or settings.sync_threshold is not None):
            @router.get("/status/{job_id}")
            @router.get("/status/{job_id}/")
            async def get_status(job_id: str) -> Dict[str, Any]:
                job = job_registry.get_job(job_id)
                if not job:
                    raise HTTPException(status_code=404, detail="Job not found")

                # Return enhanced status response with rich context
                return self._standardize_result(
                    job_id=job.job_id,
                    tool_name=schema.name,
                    status=job.status.value,
                    result=job.result or {},
                    error=job.error,
                    parameters=job.input,
                    is_job=True,
                    started_at=job.created_at.isoformat(),
                    completed_at=job.updated_at.isoformat() if job.status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED] else None,
                    status_message=job.get_status_message() if hasattr(job, 'get_status_message') else None
                )

        self._routers[schema.name] = router

    def _standardize_result(
        self,
        tool_name: str,
        status: str,
        result: Dict[str, Any],
        parameters: Dict[str, Any],
        is_job: bool,
        job_id: Optional[str] = None,
        error: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        status_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Standardize tool result format for consistent response schema"""
        # Handle different result formats
        if not isinstance(result, dict):
            result = {"value": result}

        # Build standardized result
        standardized = {
            "tool_name": tool_name,
            "status": status,
            "result": result,
            "parameters": parameters,
            "is_job": is_job
        }

        # Add optional fields if present
        if job_id:
            standardized["job_id"] = job_id
        if error:
            standardized["error"] = error
        if started_at:
            standardized["started_at"] = started_at
        if completed_at:
            standardized["completed_at"] = completed_at
        if status_message:
            standardized["status_message"] = status_message

        return standardized

    async def _run_job_in_background(self, job_id: str, implementation: Callable, kwargs: Dict[str, Any]):
        """Run a job in the background"""
        try:
            # Get current job status
            job = job_registry.get_job(job_id)

            # Only set to running if it's still pending (not already set by the caller)
            if job.status == JobStatus.PENDING:
                job_registry.update_job(job_id, JobStatus.RUNNING)

            # Run the job
            result = await implementation(**kwargs)

            # Get job details for context enrichment (refresh in case status changed)
            job = job_registry.get_job(job_id)

            # Only update if the job hasn't been cancelled
            if job.status != JobStatus.CANCELLED:
                # Standardize the result
                standardized_result = self._standardize_result(
                    job_id=job_id,
                    tool_name=job.tool_name,
                    status=JobStatus.SUCCESS.value,
                    result=result,
                    parameters=kwargs,
                    is_job=True,
                    started_at=job.created_at.isoformat(),
                    completed_at=job.updated_at.isoformat(),
                    status_message=job.get_status_message() if hasattr(job, 'get_status_message') else None
                )

                # Update job status
                job_registry.update_job(job_id, JobStatus.SUCCESS, result=standardized_result)
        except Exception as e:
            # Update job with error only if it hasn't been cancelled
            job = job_registry.get_job(job_id)
            if job and job.status != JobStatus.CANCELLED:
                job_registry.update_job(job_id, JobStatus.FAILED, error=str(e))

    def get_schema(self, name: str) -> Optional[ToolSchema]:
        """Get the schema for a tool by name."""
        return self._tools.get(name)

    def get_implementation(self, name: str) -> Optional[Callable]:
        """Get the implementation for a tool by name."""
        return self._implementations.get(name)

    def get_job_settings(self, name: str) -> Optional[JobSettings]:
        """Get the job settings for a tool by name."""
        return self._job_settings.get(name)

    def get_router(self, name: str) -> Optional[APIRouter]:
        """Get the router for a tool by name."""
        return self._routers.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

# Global registry instance
registry = ToolRegistry()

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[List[Parameter]] = None,
    settings: Optional[JobSettings] = None
) -> Callable:
    """Decorator for registering functions as tools.

    Args:
        name: Optional name for the tool. If not provided, the function name is used.
        description: Optional description of the tool. If not provided, the function's docstring is used.
        parameters: Optional list of parameters. If not provided, parameters are inferred from the function signature.
        settings: Optional job settings for the tool.
    """
    def decorator(func: Callable) -> Callable:
        # Use function name if tool name not provided
        tool_name = name or func.__name__

        # Use docstring if description not provided
        tool_description = description or (func.__doc__ or "")

        # Infer parameters from function signature if not provided
        if parameters is None:
            sig = inspect.signature(func)
            tool_parameters = []
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'job_id', 'request', 'background_tasks']:
                    continue

                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if hasattr(param.annotation, "__name__"):
                        param_type = param.annotation.__name__.lower()
                    elif hasattr(param.annotation, "_name"):
                        param_type = param.annotation._name.lower()

                tool_parameters.append(Parameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter {param_name}",
                    required=param.default == inspect.Parameter.empty
                ))
        else:
            tool_parameters = parameters

        # Create and register the tool schema
        schema = ToolSchema(
            name=tool_name,
            description=tool_description,
            parameters=tool_parameters
        )

        registry.register(schema, func, settings)
        return func

    return decorator