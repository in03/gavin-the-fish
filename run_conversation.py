#!/usr/bin/env python
"""
Run a conversation with the Gavin the Fish agent.

This script starts a conversation with the Gavin the Fish agent using the ElevenLabs SDK.
It handles audio input/output and manages the conversation lifecycle.
"""

import os
import argparse
import logging
from rich.console import Console
from rich.logging import RichHandler

from src.gavin_the_fish.conversation import GavinConversation
from src.gavin_the_fish.config import settings

# Set up rich console
console = Console()

def setup_logging(debug=False):
    """Set up logging with rich handler."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)]
    )

def main():
    """Run the conversation."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a conversation with Gavin the Fish")
    parser.add_argument("--agent-id", help="ElevenLabs agent ID (overrides environment variable)")
    parser.add_argument("--api-key", help="ElevenLabs API key (overrides environment variable)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    
    # Get agent ID and API key from arguments or environment
    agent_id = args.agent_id or settings.ELEVENLABS_AGENT_ID
    api_key = args.api_key or settings.ELEVENLABS_API_KEY
    
    # Check if agent ID is provided
    if not agent_id:
        console.print("[bold red]Error:[/bold red] Missing ElevenLabs agent ID. "
                     "Please provide it via --agent-id or set ELEVENLABS_AGENT_ID in .env")
        return 1
    
    # Create conversation manager
    try:
        conversation = GavinConversation(
            agent_id=agent_id,
            api_key=api_key,
            debug=args.debug
        )
        
        # Print instructions
        console.print("\n[bold cyan]Starting conversation with Gavin the Fish[/bold cyan]")
        console.print("Speak after the tone, or press Ctrl+C to end the conversation\n")
        
        # Start conversation
        conversation.start_conversation()
        
        # Wait for conversation to end
        conversation_id = conversation.wait_for_conversation_end()
        
        if conversation_id:
            console.print(f"\n[bold green]Conversation ended.[/bold green] ID: {conversation_id}")
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Conversation interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
