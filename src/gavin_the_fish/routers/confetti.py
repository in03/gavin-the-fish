from fastapi import APIRouter, HTTPException
import subprocess
from ..exceptions import BadRequestError

router = APIRouter(
    prefix="/confetti",
    tags=["confetti"]
)

@router.get("")
async def trigger_confetti():
    """Trigger Raycast confetti animation"""
    try:
        # Run the Raycast confetti command
        print("Triggering Raycast confetti")
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
        print(f"Error triggering confetti: {str(e)}")
        raise BadRequestError(f"Failed to trigger confetti: {str(e)}") 