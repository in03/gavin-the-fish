"""
Tool decorator module for the Gavin the Fish system.

This module contains the tool decorator and related functionality.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field
import inspect
import logging

logger = logging.getLogger(__name__)

class Parameter(BaseModel):
    """Defines a parameter for a tool."""
    name: Optional[str] = None
    type: Optional[str] = None
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    _inferred_name: Optional[str] = None
    _inferred_type: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        # If name or type are not provided, they will be set during validation
        self._inferred_name = data.get('_inferred_name')
        self._inferred_type = data.get('_inferred_type')

    def model_post_init(self, __context) -> None:
        """Set inferred values after initialization."""
        if self._inferred_name and not self.name:
            self.name = self._inferred_name
        if self._inferred_type and not self.type:
            self.type = self._inferred_type

    @classmethod
    def from_inference(cls, name: str, type: str, **kwargs) -> 'Parameter':
        """Create a Parameter instance with inferred name and type."""
        return cls(_inferred_name=name, _inferred_type=type, **kwargs)

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
        """Register a tool with the registry."""
        self._tools[schema.name] = schema
        self._implementations[schema.name] = implementation
        if settings:
            self._job_settings[schema.name] = settings

    def get_schema(self, name: str) -> Optional[ToolSchema]:
        """Get a tool schema by name."""
        return self._tools.get(name)

    def get_implementation(self, name: str) -> Optional[Callable]:
        """Get a tool implementation by name."""
        return self._implementations.get(name)

    def get_job_settings(self, name: str) -> Optional[JobSettings]:
        """Get job settings for a tool by name."""
        return self._job_settings.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

# Create a global registry instance
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
                    # If it's already a Parameter, ensure it has name and type
                    if not param_default.name:
                        param_default.name = param_name
                    if not param_default.type:
                        param_default.type = param_type
                    tool_parameters.append(param_default)
                else:
                    tool_parameters.append(Parameter.from_inference(
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
    
    return decorator 