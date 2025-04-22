#!/usr/bin/env python3
"""
Script to run tests for Gavin the Fish.

This script ensures the server is running before running the tests.
"""

import os
import sys
import time
import subprocess
import argparse
import signal
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SERVER_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")
SERVER_STARTUP_TIMEOUT = 10  # seconds

def is_server_running():
    """Check if the server is running."""
    try:
        response = httpx.get(
            f"{SERVER_URL}/jobs",
            headers={"X-API-Key": API_KEY},
            timeout=2
        )
        return response.status_code == 200
    except Exception:
        return False

def start_server():
    """Start the server in a subprocess."""
    print("Starting server...")
    server_process = subprocess.Popen(
        ["python", "-m", "src.gavin_the_fish.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid  # Create a new process group
    )
    
    # Wait for the server to start
    start_time = time.time()
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        if is_server_running():
            print("Server is running.")
            return server_process
        time.sleep(0.5)
    
    # If we get here, the server didn't start
    print("Failed to start server.")
    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
    return None

def run_tests(args):
    """Run the tests."""
    test_command = ["pytest"]
    
    # Add any additional arguments
    if args.unit:
        test_command.append("tests/unit")
    elif args.integration:
        test_command.append("tests/integration")
    elif args.file:
        test_command.append(args.file)
    
    # Add coverage if requested
    if args.coverage:
        test_command.extend(["--cov=src", "--cov-report=term"])
        if args.html:
            test_command.append("--cov-report=html")
    
    # Add verbosity
    if args.verbose:
        test_command.append("-v")
    
    # Run the tests
    print(f"Running tests: {' '.join(test_command)}")
    return subprocess.run(test_command).returncode

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests for Gavin the Fish")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--file", type=str, help="Run a specific test file")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-server", action="store_true", help="Don't start the server")
    args = parser.parse_args()
    
    server_process = None
    
    try:
        # Check if the server is already running
        if not is_server_running() and not args.no_server:
            server_process = start_server()
            if not server_process:
                return 1
        
        # Run the tests
        return run_tests(args)
        
    finally:
        # Clean up the server process if we started it
        if server_process:
            print("Stopping server...")
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)

if __name__ == "__main__":
    sys.exit(main())
