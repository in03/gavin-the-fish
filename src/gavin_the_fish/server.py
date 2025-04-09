from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
import importlib
import os
import pkgutil
from .middleware import verify_api_key
from .exceptions import ResourceNotFoundError, BadRequestError

app = FastAPI(
    title="Gavin the Fish API",
    description="API to expose Raycast scripts as webhook endpoints",
    version="1.0.0"
)

# Add API key middleware
app.middleware("http")(verify_api_key)

def create_error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "detail": detail
        }
    )

# Global exception handlers
@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    return create_error_response(exc.status_code, exc.detail)

@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError):
    return create_error_response(exc.status_code, exc.detail)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return create_error_response(exc.status_code, exc.detail)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return create_error_response(404, "Not Found")

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: Exception):
    return create_error_response(405, "Method Not Allowed")

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    return create_error_response(500, "Internal Server Error")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_error_response(422, "Validation Error")

# Dynamically import and include all routers
for module_info in pkgutil.iter_modules([os.path.join(os.path.dirname(__file__), "routers")]):
    if not module_info.name.startswith('__'):
        module = importlib.import_module(f".routers.{module_info.name}", package="gavin_the_fish")
        if hasattr(module, 'router'):
            app.include_router(module.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 