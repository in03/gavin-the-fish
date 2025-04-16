from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
import importlib
import os
import pkgutil
from .middleware import verify_api_key, log_request_metadata
from .exceptions import ResourceNotFoundError, BadRequestError
from .agent import agent
from rich.traceback import install
from rich.console import Console
from contextlib import asynccontextmanager

# Initialize Rich console and install traceback handler
console = Console()
install(show_locals=False, width=console.width)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    await agent.update_agent_tools()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Gavin the Fish API",
    description="API to expose Raycast scripts as webhook endpoints",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware in order of execution
app.middleware("http")(log_request_metadata)  # Log request metadata first
app.middleware("http")(verify_api_key)  # Then verify API key

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
    print(f"Resource not found: {exc.detail}")
    return create_error_response(exc.status_code, exc.detail)

@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError):
    print(f"Bad request: {exc.detail}")
    return create_error_response(exc.status_code, exc.detail)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print(f"HTTP exception: {exc.detail}")
    return create_error_response(exc.status_code, exc.detail)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    print("Not found")
    return create_error_response(404, "Not Found")

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: Exception):
    return create_error_response(405, "Method Not Allowed")

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    print(f"Internal server error: {str(exc)}")
    return create_error_response(500, "Internal Server Error")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {str(exc)}")
    return create_error_response(422, "Validation Error")

# Dynamically import and include all routers
for module_info in pkgutil.iter_modules([os.path.join(os.path.dirname(__file__), "tools")]):
    if not module_info.name.startswith('__'):
        module = importlib.import_module(f".tools.{module_info.name}", package="gavin_the_fish")
        if hasattr(module, 'router'):
            app.include_router(module.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 