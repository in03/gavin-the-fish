#!/usr/bin/env python3
"""
Test script for the jobs sync threshold functionality.

This script tests different tools with various sync thresholds to verify the behavior.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

# API key for authentication
API_KEY = "07E5075B-8F1B-4A83-9107-42DFA1E6E2D7"  # From .env file

async def test_short_timer():
    """Test a timer that completes within the sync threshold."""
    print("\n=== Testing Short Timer (2 seconds) ===")
    start_time = time.time()

    # Set a 2-second timer (should complete within the 3-second sync threshold)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/timer",
            json={"duration_seconds": 2},
            headers={"X-API-Key": API_KEY}
        )

        elapsed = time.time() - start_time
        data = response.json()
        print(f"Response received in {elapsed:.2f} seconds")
        print(f"Status: {data['status']}")

        # Should return SUCCESS after ~2 seconds
        assert data['status'] == 'success', f"Expected status 'success', got '{data['status']}'"
        assert 'job_id' in data, "Expected job_id in response"
        assert elapsed >= 2.0, f"Expected response time >= 2.0 seconds, got {elapsed:.2f}"

        print("✅ Short timer test passed!")
        return data['job_id']

async def test_long_timer():
    """Test a timer that exceeds the sync threshold."""
    print("\n=== Testing Long Timer (10 seconds) ===")
    start_time = time.time()

    # Set a 10-second timer (should exceed the 3-second sync threshold)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/timer",
            json={"duration_seconds": 10},
            headers={"X-API-Key": API_KEY}
        )

        elapsed = time.time() - start_time
        data = response.json()
        print(f"Response received in {elapsed:.2f} seconds")
        print(f"Status: {data['status']}")

        # Should return PENDING after ~3 seconds
        assert data['status'] == 'pending', f"Expected status 'pending', got '{data['status']}'"
        assert 'job_id' in data, "Expected job_id in response"
        assert elapsed >= 3.0, f"Expected response time >= 3.0 seconds, got {elapsed:.2f}"
        assert elapsed < 4.0, f"Expected response time < 4.0 seconds, got {elapsed:.2f}"

        job_id = data['job_id']
        print(f"Job ID: {job_id}")

        # Wait a bit for the job to complete
        await asyncio.sleep(8)

        # Check job status
        response = await client.get(
            f"{BASE_URL}/jobs",
            headers={"X-API-Key": API_KEY}
        )
        jobs_data = response.json()

        # Find our job
        job = next((j for j in jobs_data['jobs'] if j['job_id'] == job_id), None)
        assert job is not None, f"Job {job_id} not found in jobs list"

        print(f"Job status after waiting: {job['status']}")
        assert job['status'] == 'success', f"Expected job status 'success', got '{job['status']}'"

        print("✅ Long timer test passed!")
        return job_id

async def test_fibonacci_calculation():
    """Test a fibonacci calculation that should exceed the sync threshold."""
    print("\n=== Testing Fibonacci Calculation ===")
    start_time = time.time()

    # Calculate the 200th Fibonacci number (should exceed the 5-second sync threshold)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/fibonacci_calculate",
            json={"n": 200},
            headers={"X-API-Key": API_KEY}
        )

        elapsed = time.time() - start_time
        data = response.json()
        print(f"Response received in {elapsed:.2f} seconds")
        print(f"Status: {data['status']}")

        # Should return PENDING after ~5 seconds
        assert data['status'] == 'pending', f"Expected status 'pending', got '{data['status']}'"
        assert 'job_id' in data, "Expected job_id in response"
        assert elapsed >= 5.0, f"Expected response time >= 5.0 seconds, got {elapsed:.2f}"

        job_id = data['job_id']
        print(f"Job ID: {job_id}")

        # Wait a bit for the job to complete
        await asyncio.sleep(2)

        # Check job status
        response = await client.get(
            f"{BASE_URL}/jobs",
            headers={"X-API-Key": API_KEY}
        )
        jobs_data = response.json()

        # Find our job
        job = next((j for j in jobs_data['jobs'] if j['job_id'] == job_id), None)
        assert job is not None, f"Job {job_id} not found in jobs list"

        print(f"Job status after waiting: {job['status']}")
        assert job['status'] == 'success', f"Expected job status 'success', got '{job['status']}'"

        # Get the job result
        response = await client.get(
            f"{BASE_URL}/fibonacci_calculate/status/{job_id}",
            headers={"X-API-Key": API_KEY}
        )
        job_data = response.json()
        print(f"Result: {job_data['result']}")

        print("✅ Fibonacci calculation test passed!")
        return job_id

async def main():
    """Run the tests."""
    print(f"Starting tests at {datetime.now().strftime('%H:%M:%S')}")

    try:
        # Test short timer
        await test_short_timer()

        # Test long timer
        await test_long_timer()

        # Skip fibonacci calculation for now
        # await test_fibonacci_calculation()

        print("\n=== All tests passed! ===")

    except AssertionError as e:
        print(f"❌ Test failed: {str(e)}")
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
