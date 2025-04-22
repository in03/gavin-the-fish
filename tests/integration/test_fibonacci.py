"""
Integration tests for the Fibonacci calculation functionality.

These tests verify that the Fibonacci calculation tool works correctly.
"""

import pytest
import asyncio
import time

pytestmark = pytest.mark.asyncio

async def test_fibonacci_small_input(api_client):
    """Test calculating a small Fibonacci number."""
    # Calculate the 10th Fibonacci number
    response = await api_client.post(
        "/fibonacci_calculate",
        json={"n": 10}
    )
    
    data = response.json()
    assert response.status_code == 200
    assert data['status'] == 'success'
    assert 'job_id' in data
    assert data['tool_name'] == 'fibonacci_calculate'
    assert data['result']['result'] == 55  # 10th Fibonacci number is 55

async def test_fibonacci_medium_input(api_client):
    """Test calculating a medium-sized Fibonacci number."""
    # Calculate the 30th Fibonacci number
    response = await api_client.post(
        "/fibonacci_calculate",
        json={"n": 30}
    )
    
    data = response.json()
    assert response.status_code == 200
    assert 'job_id' in data
    assert data['tool_name'] == 'fibonacci_calculate'
    
    # The 30th Fibonacci number is 832040
    if data['status'] == 'success':
        assert data['result']['result'] == 832040
    else:
        # If it returned pending, wait for it to complete
        job_id = data['job_id']
        
        # Wait a bit for the job to complete
        await asyncio.sleep(2)
        
        # Check job status
        response = await api_client.get(f"/fibonacci_calculate/status/{job_id}")
        job_data = response.json()
        
        assert job_data['status'] == 'success'
        assert job_data['result']['result'] == 832040

async def test_fibonacci_invalid_input(api_client):
    """Test calculating a Fibonacci number with invalid input."""
    # Try to calculate with a negative number
    response = await api_client.post(
        "/fibonacci_calculate",
        json={"n": -1}
    )
    
    data = response.json()
    assert response.status_code == 400
    assert 'detail' in data

async def test_fibonacci_large_input(api_client):
    """Test calculating a large Fibonacci number that exceeds the sync threshold."""
    # Calculate a large Fibonacci number (5000)
    response = await api_client.post(
        "/fibonacci_calculate",
        json={"n": 5000}
    )
    
    data = response.json()
    assert response.status_code == 200
    assert 'job_id' in data
    assert data['tool_name'] == 'fibonacci_calculate'
    
    # For large inputs, we expect a pending status
    if data['status'] == 'pending':
        job_id = data['job_id']
        
        # Wait for the job to complete (with a timeout)
        max_wait = 60  # Maximum wait time in seconds
        start_wait = time.time()
        job_completed = False
        
        while time.time() - start_wait < max_wait:
            # Check job status
            response = await api_client.get(f"/fibonacci_calculate/status/{job_id}")
            job_data = response.json()
            
            if job_data['status'] in ['success', 'failed']:
                job_completed = True
                break
                
            # Wait a bit before checking again
            await asyncio.sleep(2)
        
        assert job_completed, f"Job did not complete within {max_wait} seconds"
        assert job_data['status'] == 'success'
        assert 'result' in job_data['result']
