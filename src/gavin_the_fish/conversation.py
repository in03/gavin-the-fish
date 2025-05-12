"""
Conversation management for the Gavin the Fish system.

This module provides functionality for managing conversations with the ElevenLabs agent
using the ElevenLabs SDK.
"""

import logging
import os
import signal
from typing import Optional, Callable, Dict, Any

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, AudioInterface
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

from .config import settings

# Initialize logger
logger = logging.getLogger(__name__)

class GavinConversation:
    """Manages conversations with the Gavin the Fish agent."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        api_key: Optional[str] = None,
        audio_interface: Optional[AudioInterface] = None,
        debug: bool = False
    ):
        """
        Initialize a new conversation manager.

        Args:
            agent_id: The ID of the ElevenLabs agent to use. Defaults to the one in settings.
            api_key: The ElevenLabs API key to use. Defaults to the one in settings.
            audio_interface: The audio interface to use. Defaults to DefaultAudioInterface.
            debug: Whether to enable debug logging.
        """
        self.agent_id = agent_id or settings.ELEVENLABS_AGENT_ID
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.audio_interface = audio_interface or DefaultAudioInterface()
        self.debug = debug
        self.conversation_id = None
        self.conversation = None

        # Validate required settings
        if not self.agent_id:
            raise ValueError("Missing ElevenLabs agent ID")

        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=self.api_key)

        # Set up logging
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

    def _on_agent_response(self, response: str):
        """Handle agent responses with simple logging."""
        logger.info(f"Agent: {response}")

    def _setup_conversation(self):
        """Set up the conversation with callbacks."""
        self.conversation = Conversation(
            # API client and agent ID
            self.client,
            self.agent_id,

            # Assume auth is required when API_KEY is set
            requires_auth=bool(self.api_key),

            # Use the provided audio interface
            audio_interface=self.audio_interface,

            # Simple callbacks that print the conversation to the console
            callback_agent_response=self._on_agent_response,
            callback_agent_response_correction=lambda original, corrected: logger.info(f"Agent correction: {original} -> {corrected}"),
            callback_user_transcript=lambda transcript: logger.info(f"User: {transcript}"),

            # Latency measurements if debug is enabled
            callback_latency_measurement=lambda latency: logger.debug(f"Latency: {latency}ms") if self.debug else None,
        )

    def start_conversation(self):
        """Start a new conversation with the agent."""
        if self.conversation is None:
            self._setup_conversation()

        logger.info("Starting conversation with Gavin the Fish...")
        self.conversation.start_session()

        # Set up signal handler for clean shutdown
        signal.signal(signal.SIGINT, lambda sig, frame: self.end_conversation())  # pylint: disable=unused-argument

    def end_conversation(self):
        """End the current conversation."""
        if self.conversation:
            logger.info("Ending conversation...")

            try:
                self.conversation.end_session()
                logger.info("Conversation ended successfully")
            except Exception as e:
                logger.error(f"Error ending conversation: {e}")

    def wait_for_conversation_end(self) -> Optional[str]:
        """Wait for the conversation to end and return the conversation ID."""
        if self.conversation:
            logger.info("Waiting for conversation to end...")
            try:
                self.conversation_id = self.conversation.wait_for_session_end()
                logger.info(f"Conversation ended. Conversation ID: {self.conversation_id}")
                return self.conversation_id
            except Exception as e:
                logger.error(f"Error waiting for conversation to end: {e}")
                return None
        return None
