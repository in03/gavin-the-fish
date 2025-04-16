"""
Core tool definitions and types for the Gavin the Fish system.

This package contains both core tool definitions and individual tool implementations.
The core definitions are imported here for easy access.
"""

from .core import (
    Parameter,
    ToolSchema,
    JobSettings,
    ToolRegistry,
    registry,
    tool
)

__all__ = [
    'Parameter',
    'ToolSchema',
    'JobSettings',
    'ToolRegistry',
    'registry',
    'tool'
] 