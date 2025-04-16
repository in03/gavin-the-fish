from fastapi import APIRouter, HTTPException
import subprocess
import os

router = APIRouter(
    prefix="/youtube",
    tags=["youtube"]
)

@router.post("/available")
async def check_youtube_available():
    """Check if YouTube is available"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "../../../check-youtube-available.sh")
        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        return {"message": "Success", "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 