"""
Pytest configuration for Gavin the Fish tests.
"""

import os
import pytest
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")

@pytest.fixture
def api_client():
    """Create an HTTP client with API key headers."""
    if not API_KEY:
        pytest.skip("API_KEY environment variable not set")
    
    headers = {"X-API-Key": API_KEY}
    return httpx.AsyncClient(base_url=BASE_URL, headers=headers)
