from fastapi import APIRouter, HTTPException
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(
    prefix="/xi-status",
    tags=["xi-status"]
)

class StatusItem(BaseModel):
    title: str
    status: str
    description: str
    pub_date: str

@router.get("/", response_model=List[StatusItem])
async def check_xi_status():
    """Get ElevenLabs operational status details"""
    try:
        async with httpx.AsyncClient() as client:
            # Fetch the RSS feed
            response = await client.get("https://status.elevenlabs.io/feed.rss")
            response.raise_for_status()
            
            # Parse the XML
            root = ET.fromstring(response.content)
            
            # Extract items
            items = []
            for item in root.findall(".//item"):
                title = item.find("title").text
                description = item.find("description").text
                pub_date = item.find("pubDate").text
                
                # Extract status from description
                status = "Unknown"
                if "<b>Status:" in description:
                    status = description.split("<b>Status:")[1].split("</b>")[0].strip()
                
                # Clean up description
                description = description.replace("<![CDATA[", "").replace("]]>", "")
                description = " ".join(description.split())  # Normalize whitespace
                
                items.append(StatusItem(
                    title=title,
                    status=status,
                    description=description,
                    pub_date=pub_date
                ))
            
            return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 