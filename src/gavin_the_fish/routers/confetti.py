from fastapi import APIRouter, HTTPException
import subprocess
import os
from ..exceptions import BadRequestError
from ..tool_logger import log_user_operation
router = APIRouter(
    prefix="/confetti",
    tags=["confetti"]
)

@router.get("")
@log_user_operation("Throw Confetti")
async def trigger_confetti(operation_logger):
    """Trigger Raycast confetti animation"""
    try:
        # Run the Raycast confetti command
        operation_logger.add_step("Triggering Raycast confetti")
        result = subprocess.run(
            ["open", "raycast://confetti"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise BadRequestError(f"Failed to trigger confetti: {result.stderr}")
        return {
            "status_code": 200,
            "message": "Confetti triggered!"
        }
    except Exception as e:
        operation_logger.add_step(f"Error: {str(e)}")
        raise BadRequestError(f"Failed to trigger confetti: {str(e)}") 