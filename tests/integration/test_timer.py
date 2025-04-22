"""
Integration tests for the timer functionality.

These tests verify that the timer tool works correctly.
"""

import pytest
import asyncio
import time

pytestmark = pytest.mark.asyncio

async def test_timer_creation(api_client):
    """Test creating a timer."""
    # Set a 1-second timer
    response = await api_client.post(
        "/timer",
        json={"duration_seconds": 1}
    )
    
    data = response.json()
    assert response.status_code == 200
    assert data['status'] == 'success'
    assert 'job_id' in data
    assert data['tool_name'] == 'timer'

async def test_timer_with_message(api_client):
    """Test creating a timer with a custom message."""
    # Set a 1-second timer with a custom message
    custom_message = "Custom timer message"
    response = await api_client.post(
        "/timer",
        json={
            "duration_seconds": 1,
            "message": custom_message
        }
    )
    
    data = response.json()
    assert response.status_code == 200
    assert data['status'] == 'success'
    assert 'job_id' in data
    assert data['tool_name'] == 'timer'
    assert custom_message in data['result']['message']

async def test_timer_cancellation(api_client):
    """Test cancelling a timer."""
    # Set a 10-second timer
    response = await api_client.post(
        "/timer",
        json={"duration_seconds": 10}
    )
    
    data = response.json()
    assert response.status_code == 200
    assert data['status'] == 'pending'
    assert 'job_id' in data
    
    job_id = data['job_id']
    
    # Cancel the timer
    response = await api_client.post(f"/jobs/{job_id}/cancel")
    data = response.json()
    
    assert response.status_code == 200
    assert data['status'] == 'cancelled'
    assert data['job_id'] == job_id
