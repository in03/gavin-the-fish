"""
Unit tests for the job registry.

These tests verify that the job registry works correctly.
"""

import pytest
from src.gavin_the_fish.job_registry import JobRegistry, JobStatus, Job

def test_job_creation():
    """Test creating a job."""
    registry = JobRegistry()
    job = registry.create_job(
        tool_name="test_tool",
        input={"param": "value"}
    )
    
    assert job.job_id is not None
    assert job.tool_name == "test_tool"
    assert job.input == {"param": "value"}
    assert job.status == JobStatus.PENDING

def test_job_update():
    """Test updating a job."""
    registry = JobRegistry()
    job = registry.create_job(
        tool_name="test_tool",
        input={"param": "value"}
    )
    
    # Update job status
    registry.update_job(job.job_id, JobStatus.RUNNING)
    updated_job = registry.get_job(job.job_id)
    
    assert updated_job.status == JobStatus.RUNNING
    
    # Update job with result
    result = {"output": "test_result"}
    registry.update_job(job.job_id, JobStatus.SUCCESS, result=result)
    updated_job = registry.get_job(job.job_id)
    
    assert updated_job.status == JobStatus.SUCCESS
    assert updated_job.result == result

def test_job_cancellation():
    """Test cancelling a job."""
    registry = JobRegistry()
    job = registry.create_job(
        tool_name="test_tool",
        input={"param": "value"},
        cancelable=True
    )
    
    # Cancel the job
    success = registry.cancel_job(job.job_id)
    updated_job = registry.get_job(job.job_id)
    
    assert success is True
    assert updated_job.status == JobStatus.CANCELLED
    
    # Try to cancel a non-cancelable job
    job = registry.create_job(
        tool_name="test_tool",
        input={"param": "value"},
        cancelable=False
    )
    
    success = registry.cancel_job(job.job_id)
    updated_job = registry.get_job(job.job_id)
    
    assert success is False
    assert updated_job.status == JobStatus.PENDING

def test_get_all_jobs():
    """Test getting all jobs."""
    registry = JobRegistry()
    
    # Create multiple jobs
    job1 = registry.create_job(tool_name="tool1", input={})
    job2 = registry.create_job(tool_name="tool2", input={})
    
    # Get all jobs
    jobs = registry.list_jobs()
    
    assert len(jobs) == 2
    assert job1.job_id in [j.job_id for j in jobs]
    assert job2.job_id in [j.job_id for j in jobs]
