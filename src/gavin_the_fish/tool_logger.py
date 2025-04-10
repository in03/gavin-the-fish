from functools import wraps
import logging
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install
from typing import Any, Callable, List, Optional
import inspect
import asyncio
import traceback

# Initialize Rich console and install traceback handler
console = Console()
install(show_locals=True, width=console.width)

def get_logger():
    """Get the logger instance"""
    return logging.getLogger(__name__)

def format_tool_call(func: Callable, args: tuple, kwargs: dict, result: Any = None, error: Exception = None) -> str:
    """Format tool call information into a readable string for log file"""
    # Get function signature
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    
    # Format arguments
    args_str = "\n".join(f"  {k}: {v}" for k, v in bound_args.arguments.items())
    
    # Format result or error
    result_str = ""
    if error:
        result_str = f"  Error: {str(error)}\n  Traceback:\n{traceback.format_exc()}"
    elif result is not None:
        result_str = f"  Result: {result}"
    
    return f"""
Tool Execution:
  Function: {func.__name__}
  Time: {datetime.now().isoformat()}
  Arguments:
{args_str}
{result_str}
"""

class OperationLogger:
    """Class to handle user operation logging with progress tracking"""
    def __init__(self, operation_name: str, quick: bool = False):
        self.operation_name = operation_name
        self.quick = quick
        self.steps: List[str] = []
        self.current_step: Optional[str] = None
        if not quick:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            )
            self.task_id = None

    def start(self):
        """Start the operation logging"""
        if self.quick:
            console.print(f"[cyan]{self.operation_name}[/cyan]")
        else:
            console.print(f"[cyan]Running operation: {self.operation_name}[/cyan]")
            self.progress.start()
            self.task_id = self.progress.add_task("", total=None)

    def add_step(self, step: str):
        """Add a step to the operation"""
        self.steps.append(step)
        if not self.quick and self.task_id is not None:
            self.progress.update(self.task_id, description=step)

    def complete(self):
        """Complete the operation logging"""
        if not self.quick:
            if self.task_id is not None:
                self.progress.update(self.task_id, completed=True)
            self.progress.stop()
            console.print(f"[green]Completed: {self.operation_name}[/green]")

    def error(self, error: Exception):
        """Log an error in the operation with Rich traceback"""
        if not self.quick:
            if self.task_id is not None:
                self.progress.update(self.task_id, completed=True)
            self.progress.stop()
        
        # Print the error message
        console.print(f"[red]Error in {self.operation_name}: {str(error)}[/red]")
        
        # Print the traceback with Rich formatting
        console.print_exception(show_locals=True)

def log_tool_call(func: Callable):
    """Decorator to log tool calls and their results"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log to file
            get_logger().info(format_tool_call(func, args, kwargs, result))
            
            return result
        except Exception as e:
            # Log to file
            get_logger().error(format_tool_call(func, args, kwargs, error=e))
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log to file
            get_logger().info(format_tool_call(func, args, kwargs, result))
            
            return result
        except Exception as e:
            # Log to file
            get_logger().error(format_tool_call(func, args, kwargs, error=e))
            raise
    
    # Return the appropriate wrapper based on whether the function is async
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def log_user_operation(operation_name: Optional[str] = None):
    """Decorator to log user operations with pretty printing and progress tracking"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__.replace('_', ' ').title()
            logger = OperationLogger(op_name)
            
            try:
                logger.start()
                result = await func(*args, **kwargs, operation_logger=logger)
                logger.complete()
                return result
            except Exception as e:
                logger.error(e)
                raise
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__.replace('_', ' ').title()
            logger = OperationLogger(op_name)
            
            try:
                logger.start()
                result = func(*args, **kwargs, operation_logger=logger)
                logger.complete()
                return result
            except Exception as e:
                logger.error(e)
                raise
        
        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator 