from fastapi import Request, Response
from fastapi.responses import JSONResponse
from .config import settings
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import logging
import os
from pathlib import Path
from .tool_logger import OperationLogger

# Initialize Rich console
console = Console()

# Set up logging
def setup_logging():
    # Create logs directory if it doesn't exist
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler()  # Also log to console
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# List of headers to sanitize
SENSITIVE_HEADERS = {
    settings.API_KEY_HEADER.lower(),  # API key header
    'authorization',  # Authorization header
    'cookie',  # Cookie header
    'set-cookie',  # Set-Cookie header
    'x-api-key',  # Common API key header
    'x-auth-token',  # Common auth token header
}

def sanitize_headers(headers: dict) -> dict:
    """Sanitize sensitive headers by masking their values"""
    sanitized = {}
    for header, value in headers.items():
        if header.lower() in SENSITIVE_HEADERS:
            # Get length of value and calculate asterisk portion
            if value:
                # Show first and last 2 chars, mask middle with asterisks
                sanitized[header] = value[:4] + '...' + value[-4:]
            else:
                sanitized[header] = ''
        else:
            sanitized[header] = value
    return sanitized

def format_log_entry(metadata: dict, stdout: bool = True) -> str:
    """Format metadata into a readable log entry"""
    # Format headers into a string
    headers_str = "\n".join(f"  {k}: {v}" for k, v in metadata['headers'].items())
    
    log_str = f"""
Request Details:
  Time: {metadata['timestamp']}
  Method: {metadata['method']}
  URL: {metadata['url']}
  Client: {metadata['client']['host']}:{metadata['client']['port']}
  Headers:
{headers_str}
"""
    if stdout:
        logger.info(log_str)
    else:
        # Get the file handler and log directly to it
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.emit(logging.LogRecord(
                    name=logger.name,
                    level=logging.INFO,
                    pathname=__file__,
                    lineno=0,
                    msg=log_str,
                    args=(),
                    exc_info=None
                ))
    
    return log_str

async def log_request_metadata(request: Request, call_next):
    """Middleware to log request metadata including headers"""
    # Create operation logger for this request
    operation_logger = OperationLogger("Request Logging", quick=True)
    operation_logger.start()
    
    try:
        # Get request metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "headers": sanitize_headers(dict(request.headers)),
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None
            }
        }
        
        # Create a table for the request info
        request_table = Table.grid(padding=(0, 1))
        request_table.add_row("Time:", metadata['timestamp'])
        request_table.add_row("Method:", f"[bold]{metadata['method']}[/bold]")
        request_table.add_row("URL:", f"[blue]{metadata['url']}[/blue]")
        request_table.add_row("Client:", f"{metadata['client']['host']}:{metadata['client']['port']}")
        
        # Create a table for headers
        headers_table = Table(show_header=True, header_style="bold magenta")
        headers_table.add_column("Header", style="cyan")
        headers_table.add_column("Value", style="green")
        
        for header, value in metadata['headers'].items():
            headers_table.add_row(header, value)
        
        # Print the formatted output to console
        console.print("\n")
        console.print(Panel.fit(
            request_table,
            title="[bold blue]Request Details[/bold blue]",
            border_style="blue"
        ))
        console.print("\n[bold]Headers:[/bold]")
        console.print(headers_table)
        console.print("\n")
        
        # Log detailed request info to file only
        format_log_entry(metadata, stdout=False)
        
        # Process the request
        response = await call_next(request)
        
        operation_logger.complete()
        return response
    except Exception as e:
        operation_logger.error(e)
        raise

async def verify_api_key(request: Request, call_next):
    """Middleware to verify API key in request headers"""
    # Create operation logger for this request
    operation_logger = OperationLogger("API Key Verification", quick=True)
    operation_logger.start()
    
    try:
        # Get API key from header
        api_key = request.headers.get(settings.API_KEY_HEADER)
        
        if not api_key:
            operation_logger.add_step("API key is missing")
            operation_logger.error(Exception("API key is missing"))
            return JSONResponse(
                status_code=401,
                content={
                    "status_code": 401,
                    "detail": "API key is missing"
                },
                headers={"WWW-Authenticate": "API-Key"}
            )
            
        if api_key != settings.API_KEY:
            operation_logger.add_step("Invalid API key")
            operation_logger.error(Exception("Invalid API key"))
            return JSONResponse(
                status_code=403,
                content={
                    "status_code": 403,
                    "detail": "Invalid API key"
                },
                headers={"WWW-Authenticate": "API-Key"}
            )
        
        operation_logger.add_step("API key verified")
        operation_logger.complete()
        return await call_next(request)
    except Exception as e:
        operation_logger.error(e)
        raise 