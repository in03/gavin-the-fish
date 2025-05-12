# Gavin the Fish Conversation

This directory contains scripts for running conversations with the Gavin the Fish agent using the ElevenLabs SDK.

## Prerequisites

- Python 3.8 or higher
- ElevenLabs API key
- ElevenLabs agent ID
- PyAudio, PortAudio (macOS)

## Setup

1. Make sure you have the required dependencies installed:

```bash
uv sync
```

2. Set up your environment variables in `.env`:

```
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here
```

## Simple Usage (No PyAudio Required)

Run a simple conversation with the agent without requiring PyAudio:

```bash
./run_simple_conversation.py
```

This will start a conversation with the agent using the ElevenLabs SDK directly.

## Basic Usage (Requires PyAudio)

Run a basic conversation with the agent:

```bash
./run_conversation.py
```

This will start a conversation with the agent using the default audio devices.

## Enhanced Usage (Requires PyAudio)

Run an enhanced conversation with volume visualization:

```bash
./run_enhanced_conversation.py
```

### Command Line Options

Both scripts support the following command line options:

- `--agent-id`: Override the ElevenLabs agent ID from the environment
- `--api-key`: Override the ElevenLabs API key from the environment
- `--debug`: Enable debug logging

The enhanced script also supports:

- `--input-device`: Specify the input device index
- `--output-device`: Specify the output device index
- `--list-devices`: List available audio devices

Example:

```bash
./run_enhanced_conversation.py --list-devices
./run_enhanced_conversation.py --input-device 1 --output-device 2
```

## How It Works

The conversation scripts use the ElevenLabs SDK to:

1. Connect to the ElevenLabs API
2. Start a conversation session with the agent
3. Handle audio input from the microphone
4. Stream audio output to the speakers
5. Process the conversation until it ends or is interrupted

The enhanced version adds:

- Volume level visualization
- Custom audio device selection
- More detailed feedback

## Troubleshooting

If you encounter issues:

1. Make sure your API key and agent ID are correct
2. If using audio scripts, check that your microphone and speakers are working
3. If you have issues with PyAudio installation:
   ```bash
   # Install PortAudio library first
   brew install portaudio

   # Then try installing with explicit paths
   CFLAGS="-I/opt/homebrew/include" LDFLAGS="-L/opt/homebrew/lib" uv sync
   ```
4. Try listing available audio devices and selecting specific ones
5. Enable debug logging with the `--debug` flag
6. If all else fails, use the simple conversation script that doesn't require PyAudio

## Advanced Customization

You can customize the audio interface by modifying the `CustomAudioInterface` class in `src/gavin_the_fish/custom_audio_interface.py`.

For more advanced customization, see the ElevenLabs SDK documentation.
