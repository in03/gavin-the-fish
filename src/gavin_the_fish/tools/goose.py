"""
Goose tool for generating random goose-related content.

This tool provides various goose-related functionalities.
"""

import logging
from typing import Dict, Any
from .core import tool, Parameter, JobSettings
import subprocess
from rich.console import Console

# Initialize console
console = Console()

logger = logging.getLogger(__name__)

@tool(
    name="goose",
    description="Run a Goose MCP command on a specified target.",
    settings=JobSettings(
        sync_threshold=5,
        job_timeout=0,
        notify_title="Goose Command Complete",
        notify_message="Goose command completed for target {target}",
        cancelable=True
    )
)
async def run_goose_command(
    text: str = Parameter(
        name="text",
        type="string",
        description="Query, prompt or command to run with Goose.",
        required=True
    )
) -> dict:
    """Run a Goose MCP command on the specified target"""
    try:
        # Run the goose command
        process = subprocess.run(
            ["goose", "run", "-t", text],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "text": text,
            "output": process.stdout.strip()
        }
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Command failed: {e.stderr.strip()}")
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")

