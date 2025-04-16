"""
Core tool definitions and types for the Gavin the Fish system.

This module contains the fundamental building blocks for tool definitions:
- Parameter: Defines the structure of tool parameters
- ToolSchema: Defines the structure of tool definitions
- JobSettings: Defines job execution settings
- ToolRegistry: Manages tool registration and lookup
- tool decorator: Decorator for registering functions as tools
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field
from enum import Enum
import inspect
import logging
import uuid

logger = logging.getLogger(__name__)

T = TypeVar("T")

class Parameter(BaseModel):
    """Defines a parameter for a tool."""
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None

class ToolSchema(BaseModel):
    """Defines the schema for a tool."""
    name: str
    description: str
    parameters: List[Parameter]

class JobSettings(BaseModel):
    """Defines settings for job execution."""
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None

class ToolRegistry:
    """Registry for managing tools."""
    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._implementations: Dict[str, Callable] = {}
        self._job_settings: Dict[str, JobSettings] = {}

    def register(self, schema: ToolSchema, implementation: Callable, settings: Optional[JobSettings] = None) -> None:
        """Register a tool with its schema and implementation."""
        self._tools[schema.name] = schema
        self._implementations[schema.name] = implementation
        if settings:
            self._job_settings[schema.name] = settings

    def get_schema(self, name: str) -> Optional[ToolSchema]:
        """Get the schema for a tool by name."""
        return self._tools.get(name)

    def get_implementation(self, name: str) -> Optional[Callable]:
        """Get the implementation for a tool by name."""
        return self._implementations.get(name)

    def get_job_settings(self, name: str) -> Optional[JobSettings]:
        """Get the job settings for a tool by name."""
        return self._job_settings.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

# Global registry instance
registry = ToolRegistry()

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[List[Parameter]] = None,
    settings: Optional[JobSettings] = None
) -> Callable:
    """Decorator for registering functions as tools.
    
    Args:
        name: Optional name for the tool. If not provided, the function name is used.
        description: Optional description of the tool. If not provided, the function's docstring is used.
        parameters: Optional list of parameters. If not provided, parameters are inferred from the function signature.
        settings: Optional job settings for the tool.
    """
    def decorator(func: Callable) -> Callable:
        # Use function name if tool name not provided
        tool_name = name or func.__name__
        
        # Use docstring if description not provided
        tool_description = description or (func.__doc__ or "")
        
        # Infer parameters from function signature if not provided
        if parameters is None:
            sig = inspect.signature(func)
            tool_parameters = []
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param_name == "job_id":
                    continue
                    
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if hasattr(param.annotation, "__name__"):
                        param_type = param.annotation.__name__.lower()
                    elif hasattr(param.annotation, "_name"):
                        param_type = param.annotation._name.lower()
                
                # Get the Parameter instance if it exists
                param_default = param.default
                if isinstance(param_default, Parameter):
                    tool_parameters.append(param_default)
                else:
                    tool_parameters.append(Parameter(
                        name=param_name,
                        type=param_type,
                        description=f"Parameter {param_name}",
                        required=param.default == inspect.Parameter.empty
                    ))
        else:
            tool_parameters = parameters

        # Create and register the tool schema
        schema = ToolSchema(
            name=tool_name,
            description=tool_description,
            parameters=tool_parameters
        )
        
        registry.register(schema, func, settings)
        return func 