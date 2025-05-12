#!/usr/bin/env python
"""
Run an enhanced conversation with the Gavin the Fish agent.

This script starts a conversation with the Gavin the Fish agent using the ElevenLabs SDK
and provides a simple visualization of the audio levels.
"""

import os
import argparse
import logging
import time
import threading
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, BarColumn, TextColumn

from src.gavin_the_fish.conversation import GavinConversation
from src.gavin_the_fish.custom_audio_interface import CustomAudioInterface
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

def list_audio_devices():
    """List available audio devices."""
    devices = CustomAudioInterface.list_audio_devices()
    
    console.print("\n[bold cyan]Available Audio Devices:[/bold cyan]")
    console.print("[bold]Input Devices:[/bold]")
    for device in devices:
        if device['input_channels'] > 0:
            default_marker = " [bold green](default)[/bold green]" if device['is_default_input'] else ""
            console.print(f"  {device['index']}: {device['name']}{default_marker}")
    
    console.print("\n[bold]Output Devices:[/bold]")
    for device in devices:
        if device['output_channels'] > 0:
            default_marker = " [bold green](default)[/bold green]" if device['is_default_output'] else ""
            console.print(f"  {device['index']}: {device['name']}{default_marker}")
    
    console.print()

def main():
    """Run the enhanced conversation."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run an enhanced conversation with Gavin the Fish")
    parser.add_argument("--agent-id", help="ElevenLabs agent ID (overrides environment variable)")
    parser.add_argument("--api-key", help="ElevenLabs API key (overrides environment variable)")
    parser.add_argument("--input-device", type=int, help="Input device index")
    parser.add_argument("--output-device", type=int, help="Output device index")
    parser.add_argument("--list-devices", action="store_true", help="List available audio devices")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    
    # List audio devices if requested
    if args.list_devices:
        list_audio_devices()
        return 0
    
    # Get agent ID and API key from arguments or environment
    agent_id = args.agent_id or settings.ELEVENLABS_AGENT_ID
    api_key = args.api_key or settings.ELEVENLABS_API_KEY
    
    # Check if agent ID is provided
    if not agent_id:
        console.print("[bold red]Error:[/bold red] Missing ElevenLabs agent ID. "
                     "Please provide it via --agent-id or set ELEVENLABS_AGENT_ID in .env")
        return 1
    
    # Create audio interface with volume visualization
    current_volume = 0.0
    
    def update_volume(volume):
        nonlocal current_volume
        current_volume = volume
    
    # Create audio interface
    audio_interface = CustomAudioInterface(
        input_device_index=args.input_device,
        output_device_index=args.output_device,
        on_volume_change=update_volume
    )
    
    # Create conversation manager
    try:
        conversation = GavinConversation(
            agent_id=agent_id,
            api_key=api_key,
            audio_interface=audio_interface,
            debug=args.debug
        )
        
        # Print instructions
        console.print("\n[bold cyan]Starting enhanced conversation with Gavin the Fish[/bold cyan]")
        console.print("Speak after the tone, or press Ctrl+C to end the conversation\n")
        
        # Start volume visualization in a separate thread
        stop_visualization = threading.Event()
        
        def run_visualization():
            with Progress(
                TextColumn("[bold blue]Volume:[/bold blue]"),
                BarColumn(bar_width=40),
                TextColumn("[bold]{task.percentage:.0f}%[/bold]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("", total=100)
                while not stop_visualization.is_set():
                    progress.update(task, completed=current_volume * 100)
                    time.sleep(0.05)
        
        visualization_thread = threading.Thread(target=run_visualization)
        visualization_thread.daemon = True
        visualization_thread.start()
        
        # Start conversation
        conversation.start_conversation()
        
        # Wait for conversation to end
        conversation_id = conversation.wait_for_conversation_end()
        
        # Stop visualization
        stop_visualization.set()
        visualization_thread.join(timeout=1.0)
        
        if conversation_id:
            console.print(f"\n[bold green]Conversation ended.[/bold green] ID: {conversation_id}")
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Conversation interrupted by user[/bold yellow]")
        stop_visualization.set() if 'stop_visualization' in locals() else None
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        stop_visualization.set() if 'stop_visualization' in locals() else None
        return 1
    finally:
        # Clean up audio interface
        if 'audio_interface' in locals():
            audio_interface.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())
