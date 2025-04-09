from fastapi import APIRouter, HTTPException
import subprocess
import os
from pydantic import BaseModel

router = APIRouter(
    prefix="/gift-credits",
    tags=["gift-credits"]
)

class GiftCreditsRequest(BaseModel):
    total_credits: str

@router.post("/")
async def gift_credits(request: GiftCreditsRequest):
    """Gift credits to a user"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "../../../gift_credits.py")
        result = subprocess.run(
            [script_path, request.total_credits],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        return {"message": "Success", "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 