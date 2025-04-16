"""
Core agent management and tool registration.

This module provides the core Agent class which:
- Maintains a registry of available tools
- Handles tool registration and validation
- Manages updates to external services (e.g., ElevenLabs)
- Provides methods for tool lookup and execution

The Agent class works with the core tool definitions from tools.core
and uses the tool registration functions from agent_tools.py.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable
from pydantic import BaseModel, Field
import httpx
import asyncio
from .tools import Parameter, ToolSchema, JobSettings, ToolRegistry, registry, tool
from .config import settings

class Agent:
    """Central agent class for managing tools and agent configuration."""
    
    def __init__(self, name: str):
        self.name = name
        self._tools: Dict[str, ToolSchema] = {}
    
    def tool(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Parameter]] = None
    ) -> Callable:
        """
        Decorator for defining a tool.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
            parameters: Optional dictionary of parameter definitions
        """
        def decorator(func: Callable) -> Callable:
            # Get the function's signature for parameter info
            from inspect import signature
            sig = signature(func)
            
            # Build the parameter schema
            param_schema = parameters or {}
            for param_name, param in sig.parameters.items():
                if param_name in ['request', 'background_tasks']:  # Skip FastAPI-specific params
                    continue
                    
                if param_name not in param_schema:
                    param_type = param.annotation
                    if param_type == param.empty:
                        param_type = str
                        
                    param_schema[param_name] = Parameter(
                        type=_get_type_name(param_type),
                        description=f"Parameter {param_name}",
                        required=param.default == param.empty
                    )
            
            # Create the tool schema
            tool_schema = ToolSchema(
                name=name,
                description=description,
                parameters=param_schema
            )
            
            # Store the tool schema
            self._tools[name] = tool_schema
            
            # Return the original function
            return func
        
        return decorator
    
    async def update_agent_tools(self):
        """Update the ElevenLabs agent with the registered tools."""
        if not settings.ELEVENLABS_API_KEY or not settings.ELEVENLABS_AGENT_ID:
            return
            
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Convert tools to ElevenLabs format
        tools = []
        for schema in self._tools.values():
            parameters = {
                name: {
                    "type": param.type,
                    "description": param.description,
                    "required": param.required
                }
                for name, param in schema.parameters.items()
            }
            
            tools.append({
                "name": schema.name,
                "description": schema.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": [name for name, param in parameters.items() if param["required"]]
                }
            })
        
        async with httpx.AsyncClient(headers=headers) as client:
            url = f"{settings.ELEVENLABS_API_BASE_URL}/convai/agents/{settings.ELEVENLABS_AGENT_ID}"
            response = await client.patch(url, json={"tools": tools})
            response.raise_for_status()

def _get_type_name(type_obj: Type) -> str:
    """Convert Python type to JSON schema type name."""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }
    return type_map.get(type_obj, "string")

# Global agent instance
agent = Agent("Gavin the Fish") 