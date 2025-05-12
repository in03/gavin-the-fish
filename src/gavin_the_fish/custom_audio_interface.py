"""
Custom audio interface implementations for the Gavin the Fish system.

This module provides custom audio interface implementations for use with the ElevenLabs SDK.
"""

import logging
import queue
import threading
import time
from typing import Optional, Callable, Dict, Any, List

import numpy as np
import pyaudio
from elevenlabs.conversational_ai.conversation import AudioInterface

# Initialize logger
logger = logging.getLogger(__name__)

class CustomAudioInterface(AudioInterface):
    """
    Custom audio interface implementation with additional features.

    This implementation extends the default audio interface with:
    - Volume level monitoring
    - Audio visualization capabilities
    - Customizable audio parameters
    - Echo suppression for better interruption handling
    """

    def start(self, input_callback=None) -> None:
        """Start the audio interface (required abstract method).

        Args:
            input_callback: Optional callback function for audio input processing.
        """
        self.start_recording()
        # Store the callback for potential future use
        self.input_callback = input_callback

    def stop(self) -> None:
        """Stop the audio interface (required abstract method)."""
        self.stop_recording()
        if self.output_stream and self.output_stream.is_active():
            try:
                self.output_stream.stop_stream()
            except Exception as e:
                logger.error(f"Error stopping output stream: {e}")

    def output(self, audio_data: bytes) -> None:
        """Output audio data (required abstract method)."""
        # This method is called by the ElevenLabs SDK
        logger.debug("Outputting audio data")
        self.play_audio(audio_data)

    def interrupt(self) -> None:
        """Interrupt audio processing (required abstract method)."""
        # Stop any ongoing audio playback
        if self.output_stream and self.is_playing and self.output_stream.is_active():
            try:
                self.output_stream.stop_stream()
            except Exception as e:
                logger.error(f"Error interrupting output stream: {e}")
            finally:
                self.is_playing = False

    def __init__(
        self,
        input_device_index: Optional[int] = None,
        output_device_index: Optional[int] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        format_type: int = pyaudio.paInt16,
        on_volume_change: Optional[Callable[[float], None]] = None
    ):
        """
        Initialize the custom audio interface.

        Args:
            input_device_index: Index of the input device to use. None for default.
            output_device_index: Index of the output device to use. None for default.
            sample_rate: Sample rate to use for audio.
            channels: Number of channels to use for audio.
            chunk_size: Chunk size to use for audio processing.
            format_type: Format type to use for audio.
            on_volume_change: Callback for volume level changes.
        """
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format_type = format_type
        self.on_volume_change = on_volume_change

        # Audio processing state
        self.p = None
        self.input_stream = None
        self.output_stream = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.is_playing = False
        self.current_volume = 0.0
        self.input_callback = None

        # Echo suppression parameters
        self.recent_output_audio = []
        self.echo_suppression_enabled = True
        self.noise_gate_threshold = 0.02  # Minimum volume to consider as actual speech
        self.echo_attenuation = 0.7       # How much to attenuate detected echo

        # Initialize PyAudio
        self.p = pyaudio.PyAudio()

    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        if self.is_recording:
            return

        def callback(in_data, frame_count, time_info, status):  # pylint: disable=unused-argument
            if self.is_recording:
                # Convert input to numpy array for processing
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                processed_data = in_data  # Default to original data

                # Apply echo suppression if enabled and we're playing audio
                if self.echo_suppression_enabled and self.is_playing and len(self.recent_output_audio) > 0:
                    try:
                        # Simple echo suppression: apply noise gate during playback
                        # Calculate volume level
                        if len(audio_data) > 0:
                            mean_square = np.mean(np.square(audio_data))
                            if mean_square > 0:
                                rms = np.sqrt(mean_square)
                                normalized_rms = min(1.0, rms / 32767.0)  # Normalize to 0.0-1.0

                                # Apply noise gate - only pass audio if it's louder than threshold
                                # This helps distinguish between echo and actual user speech
                                if normalized_rms < self.noise_gate_threshold:
                                    # Likely echo or background noise, attenuate it
                                    audio_data = (audio_data * (1.0 - self.echo_attenuation)).astype(np.int16)
                                else:
                                    # Likely actual speech, keep it
                                    logger.debug(f"Detected potential user interruption: volume={normalized_rms}")

                        processed_data = audio_data.tobytes()
                    except Exception as e:
                        logger.error(f"Error in echo suppression: {e}")
                        processed_data = in_data  # Fallback to original data

                # Put processed audio in queue
                self.audio_queue.put(processed_data)

                # Calculate volume level (RMS) for visualization
                if self.on_volume_change:
                    # We already have audio_data from above
                    if not isinstance(audio_data, np.ndarray):
                        audio_data = np.frombuffer(in_data, dtype=np.int16)

                    # Check for empty or invalid audio data to prevent warnings
                    if len(audio_data) > 0:
                        # Use a small epsilon to avoid sqrt of zero
                        mean_square = np.mean(np.square(audio_data))
                        if mean_square > 0:
                            rms = np.sqrt(mean_square)
                            normalized_rms = min(1.0, rms / 32767.0)  # Normalize to 0.0-1.0
                            self.current_volume = normalized_rms
                            self.on_volume_change(normalized_rms)
                        else:
                            self.current_volume = 0.0
                            self.on_volume_change(0.0)
                    else:
                        self.current_volume = 0.0
                        self.on_volume_change(0.0)

                # Call the input callback if provided
                if self.input_callback:
                    self.input_callback(processed_data)

            return (in_data, pyaudio.paContinue)

        self.input_stream = self.p.open(
            format=self.format_type,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=callback
        )

        self.is_recording = True
        logger.debug("Started recording")

    def stop_recording(self) -> None:
        """Stop recording audio from the microphone."""
        self.is_recording = False
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None
        logger.debug("Stopped recording")

    def read_audio(self, chunk_size: int) -> bytes:
        """Read audio data from the microphone."""
        if not self.is_recording:
            self.start_recording()

        try:
            return self.audio_queue.get(block=True, timeout=0.1)
        except queue.Empty:
            return b'\x00' * chunk_size * self.channels * 2  # Return silence

    def play_audio(self, audio_data: bytes) -> None:
        """Play audio data through the speakers with echo suppression."""
        # Store the output audio for echo suppression
        try:
            # Convert to numpy array for later processing
            output_data = np.frombuffer(audio_data, dtype=np.int16)
            # Store in recent output buffer (limit to last 5 chunks to save memory)
            self.recent_output_audio.append(output_data)
            if len(self.recent_output_audio) > 5:
                self.recent_output_audio.pop(0)  # Remove oldest chunk
        except Exception as e:
            logger.error(f"Error storing output audio for echo suppression: {e}")

        # Create output stream if needed
        if self.output_stream is None:
            # Create a non-callback output stream for direct writing
            self.output_stream = self.p.open(
                format=self.format_type,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.chunk_size
                # No stream_callback for direct writing
            )

        # Play the audio
        self.is_playing = True
        try:
            self.output_stream.write(audio_data)
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
        finally:
            self.is_playing = False

        # Clear the output buffer after a short delay
        # This helps prevent echo suppression from affecting subsequent user input
        def clear_output_buffer():
            time.sleep(0.5)  # Wait for echo to fade
            self.recent_output_audio = []

        # Start a thread to clear the buffer
        threading.Thread(target=clear_output_buffer, daemon=True).start()

    def set_echo_suppression(self, enabled: bool, threshold: float = None, attenuation: float = None) -> None:
        """Enable or disable echo suppression.

        Args:
            enabled: Whether to enable echo suppression
            threshold: Optional noise gate threshold (0.0-1.0)
            attenuation: Optional echo attenuation factor (0.0-1.0)
        """
        self.echo_suppression_enabled = enabled
        if threshold is not None:
            self.noise_gate_threshold = max(0.0, min(1.0, threshold))
        if attenuation is not None:
            self.echo_attenuation = max(0.0, min(1.0, attenuation))

        logger.info(f"Echo suppression {'enabled' if enabled else 'disabled'} "
                   f"(threshold={self.noise_gate_threshold}, attenuation={self.echo_attenuation})")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_recording()

        if self.output_stream:
            try:
                if self.output_stream.is_active():
                    self.output_stream.stop_stream()
                self.output_stream.close()
            except Exception as e:
                logger.error(f"Error cleaning up output stream: {e}")
            finally:
                self.output_stream = None

        if self.p:
            try:
                self.p.terminate()
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            finally:
                self.p = None

        logger.debug("Audio interface cleaned up")

    @staticmethod
    def list_audio_devices() -> List[Dict[str, Any]]:
        """List available audio devices."""
        p = pyaudio.PyAudio()
        devices = []

        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': device_info['name'],
                'input_channels': device_info['maxInputChannels'],
                'output_channels': device_info['maxOutputChannels'],
                'default_sample_rate': device_info['defaultSampleRate'],
                'is_default_input': p.get_default_input_device_info()['index'] == i,
                'is_default_output': p.get_default_output_device_info()['index'] == i
            })

        p.terminate()
        return devices
