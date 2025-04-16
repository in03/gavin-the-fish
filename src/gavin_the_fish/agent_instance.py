"""
Global agent instance management.

This module provides the global agent instance that can be imported by other modules
without creating circular dependencies.
"""

from .agent import Agent

# Global agent instance
agent = Agent("Gavin the Fish") 