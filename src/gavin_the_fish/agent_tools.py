"""
Integration layer for FastAPI and ElevenLabs tool management.

This module serves as the integration point between FastAPI endpoints and the
agent tool system. It provides:

- Tool registration functions that handle both FastAPI routing and agent registration
- Conversion between FastAPI endpoints and ElevenLabs tool formats
- Synchronization of tool definitions with external services

The module works with the core Agent class from agent.py and uses the types
defined in tools.py to ensure consistent tool definitions across the system.

This module is typically used by router modules to register their endpoints
as tools while maintaining proper integration with both FastAPI and ElevenLabs.
"""

from typing import Dict, List, Optional, Type, Any
from fastapi import APIRouter
import httpx
from .config import settings
from .tools import ToolSchema
from .agent_instance import agent

def register_tool(
    router: APIRouter,
    endpoint_func: callable,
    path: str,
    method: str,
    schema: ToolSchema
):
    """Register a FastAPI endpoint as an ElevenLabs tool."""
    # Convert the tool schema to the format expected by ElevenLabs
    parameters = {
        name: {
            "type": param.type,
            "description": param.description,
            "required": param.required
        }
        for name, param in schema.parameters.items()
    }
    
    # Register with the agent
    agent.tool(
        name=schema.name,
        description=schema.description,
        parameters=schema.parameters
    )(endpoint_func)
    
    # Register with FastAPI router
    getattr(router, method.lower())(path)(endpoint_func)

async def update_agent_tools():
    """Update the ElevenLabs agent with the registered tools."""
    await agent.update_agent_tools() 