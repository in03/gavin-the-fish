from fastapi import APIRouter, HTTPException
import subprocess
import os
from typing import Optional
from pydantic import BaseModel

router = APIRouter(
    prefix="/zendesk-ticket",
    tags=["zendesk-ticket"]
)

class ZendeskTicketRequest(BaseModel):
    ticket_number: Optional[str] = None

@router.post("/info")
async def paste_zendesk_ticket_info(request: ZendeskTicketRequest):
    """Paste Zendesk ticket information"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "../../../paste-zendesk-ticket-info.sh")
        args = []
        if request.ticket_number:
            args.append(request.ticket_number)
        
        result = subprocess.run(
            [script_path] + args,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
        return {"message": "Success", "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 