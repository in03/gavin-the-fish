#!/usr/bin/env python
"""
Run a simple conversation with the Gavin the Fish agent.

This script starts a conversation with the Gavin the Fish agent using the ElevenLabs SDK.
It uses a simplified approach that doesn't require PyAudio.
"""

import os
import argparse
import logging
import signal
import sys
from rich.console import Console
from rich.logging import RichHandler

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation

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
    """Run the simple conversation."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a simple conversation with Gavin the Fish")
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
    
    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=api_key)
    
    # Create conversation
    try:
        # Print instructions
        console.print("\n[bold cyan]Starting conversation with Gavin the Fish[/bold cyan]")
        console.print("This is a simplified version that uses the ElevenLabs SDK directly.")
        console.print("Press Ctrl+C to end the conversation\n")
        
        # Set up callbacks
        def on_agent_response(response):
            console.print(f"[bold green]Agent:[/bold green] {response}")
        
        def on_user_transcript(transcript):
            console.print(f"[bold blue]User:[/bold blue] {transcript}")
        
        def on_correction(original, corrected):
            console.print(f"[bold yellow]Correction:[/bold yellow] {original} -> {corrected}")
        
        # Create conversation
        conversation = Conversation(
            client,
            agent_id,
            requires_auth=bool(api_key),
            callback_agent_response=on_agent_response,
            callback_agent_response_correction=on_correction,
            callback_user_transcript=on_user_transcript,
        )
        
        # Set up signal handler for clean shutdown
        def handle_interrupt(sig, frame):
            console.print("\n[bold yellow]Ending conversation...[/bold yellow]")
            conversation.end_session()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_interrupt)
        
        # Start conversation
        console.print("[bold]Starting session...[/bold]")
        conversation.start_session()
        
        # Wait for conversation to end
        conversation_id = conversation.wait_for_session_end()
        
        console.print(f"\n[bold green]Conversation ended.[/bold green] ID: {conversation_id}")
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Conversation interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
