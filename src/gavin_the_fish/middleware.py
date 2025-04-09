from fastapi import Request, Response
from fastapi.responses import JSONResponse
from .config import settings

async def verify_api_key(request: Request, call_next):
    """Middleware to verify API key in request headers"""
    # Get API key from header
    api_key = request.headers.get(settings.API_KEY_HEADER)
    
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={
                "status_code": 401,
                "detail": "API key is missing"
            },
            headers={"WWW-Authenticate": "API-Key"}
        )
        
    if api_key != settings.API_KEY:
        return JSONResponse(
            status_code=403,
            content={
                "status_code": 403,
                "detail": "Invalid API key"
            },
            headers={"WWW-Authenticate": "API-Key"}
        )
    
    return await call_next(request) 