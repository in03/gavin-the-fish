"""
Fibonacci sequence generator tool.

This tool generates a Fibonacci sequence of a specified length.
"""

import logging
from typing import Dict, Any
from .core import tool, Parameter, JobSettings
from rich.console import Console

# Initialize console
console = Console()

logger = logging.getLogger(__name__)

def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number"""
    if n <= 0:
        raise ValueError("Input must be a positive integer")
    elif n == 1 or n == 2:
        return 1
    else:
        a, b = 1, 1
        for _ in range(3, n + 1):
            a, b = b, a + b
        return b

@tool(
    name="fibonacci",
    description="Generate a Fibonacci sequence of specified length",
    parameters=[
        Parameter(
            name="N",
            type="integer",
            description="Length of the Fibonacci sequence to generate",
            required=True
        )
    ],
    settings=JobSettings(
        timeout_seconds=30,
        max_retries=3,
        retry_delay_seconds=5
    )
)
async def generate_fibonacci(N: int) -> Dict[str, Any]:
    """Generate a Fibonacci sequence of length N."""
    if N < 0:
        raise ValueError("N must be a non-negative integer")

    sequence = [0, 1]
    if N <= 2:
        return {"sequence": sequence[:N]}

    for i in range(2, N):
        next_num = sequence[i-1] + sequence[i-2]
        sequence.append(next_num)

    return {"sequence": sequence}

@tool(
    name="fibonacci_calculate",
    description="Calculate the nth Fibonacci number.",
    settings=JobSettings(
        sync_threshold=5,
        job_timeout=0,
        notify_title="Fibonacci Calculation Complete",
        notify_message="Fibonacci calculation completed for n={n}",
        cancelable=True
    )
)
async def run_fibonacci_calculation(n: int) -> dict:
    """Calculate the nth Fibonacci number"""
    # Validate input - allow much larger numbers but set a reasonable limit
    # 100,000 should take a few minutes on modern hardware for large values
    if n > 100000:
        raise ValueError("Input too large - please use n <= 100000")

    # Calculate Fibonacci number
    result = calculate_fibonacci(n)

    return {
        "n": n,
        "result": result
    }