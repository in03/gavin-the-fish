"""
Unit tests for the tool registry.

These tests verify that the tool registry works correctly.
"""

import pytest
from src.gavin_the_fish.tools.core import ToolRegistry, ToolSchema, Parameter, JobSettings

def test_tool_registration():
    """Test registering a tool."""
    registry = ToolRegistry()
    
    # Create a tool schema
    schema = ToolSchema(
        name="test_tool",
        description="Test tool",
        parameters=[
            Parameter(
                name="param1",
                type="string",
                description="Test parameter",
                required=True
            )
        ]
    )
    
    # Create a mock implementation
    async def implementation(param1: str):
        return {"result": param1}
    
    # Register the tool
    registry.register(schema, implementation)
    
    # Verify the tool was registered
    assert "test_tool" in registry.list_tools()
    assert registry.get_schema("test_tool") == schema
    assert registry.get_implementation("test_tool") == implementation

def test_tool_registration_with_settings():
    """Test registering a tool with job settings."""
    registry = ToolRegistry()
    
    # Create a tool schema
    schema = ToolSchema(
        name="test_tool",
        description="Test tool",
        parameters=[
            Parameter(
                name="param1",
                type="string",
                description="Test parameter",
                required=True
            )
        ]
    )
    
    # Create job settings
    settings = JobSettings(
        sync_threshold=5,
        job_timeout=30,
        cancelable=True
    )
    
    # Create a mock implementation
    async def implementation(param1: str):
        return {"result": param1}
    
    # Register the tool with settings
    registry.register(schema, implementation, settings)
    
    # Verify the tool and settings were registered
    assert "test_tool" in registry.list_tools()
    assert registry.get_schema("test_tool") == schema
    assert registry.get_implementation("test_tool") == implementation
    assert registry.get_job_settings("test_tool") == settings
