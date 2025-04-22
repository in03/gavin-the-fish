"""
Agent management for the Gavin the Fish system.

This module provides functionality for managing the ElevenLabs agent
and updating its configuration.
"""

import logging
from typing import Dict, Optional
from rich.console import Console
from .config import settings
import json
from pathlib import Path
from elevenlabs import ElevenLabs

# Initialize logger and console
logger = logging.getLogger(__name__)
console = Console()

if not settings.ELEVENLABS_API_KEY or not settings.ELEVENLABS_AGENT_ID:
    logger.error("Missing ElevenLabs API key or agent ID")
    raise ValueError("Missing ElevenLabs API key or agent ID")

# Initialize ElevenLabs client and agent
client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
agent = client.conversational_ai.get_agent(settings.ELEVENLABS_AGENT_ID)

async def update_agent_tools():
    """Update the ElevenLabs agent with the configuration from agent_config.json."""
        
    # Read the agent config file
    config_file = Path("agent_config.json")
    if not config_file.exists():
        logger.error("agent_config.json not found")
        return
        
    with config_file.open() as f:
        config = json.load(f)
        
    logger.info(f"Found config with {len(config['conversation_config']['agent']['prompt']['tools'])} tools")
    
    try:
        # Update the agent using the SDK
        updated_agent = client.conversational_ai.update_agent(**config)
        # logger.info("Successfully patched agent with config")
        # with open("current_agent_config.json", "w")  as f:
        #     f.write(updated_agent.json())
        
    except Exception as e:
        logger.error(f"Failed to patch agent: {str(e)}")
        raise 