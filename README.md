# Gavin-The-Fish
**Gavin the Fish** is a handy but snarky little automation expert built with 11L Conversational AI, FastAPI, Raycast and some nifty scripts.

> [!Warning] 
> 🚧 Work in progress! Just testing some cheeky tricks!

## Setup
1. Clone the repository
2. Install Python 3.13 or higher
3. Install dependencies:
   ```bash
   # Using uv (recommended)
   uv sync
   uv pip install -e .
   ```
4. Set up your environment variables in `.env`:
   - Define whatever you like as your API key. Recommend a UUID.

## Installation
1. Install the Raycast extension
2. Configure your agent
3. Start the FastAPI server:
   ```bash
   python run_server.py
   ```
4. Use ngrok or Cloudflare to expose your local server:
   ```bash
   ngrok http 8000
   ```
5. Add the reverse proxy / forwarding URL with the tool endpoints in your Conversational AI Agent.
    - Recommend testing with curl:
    ```bash
     curl -X GET "http://localhost:8000/confetti" \
     -H "X-API-Key: the-api-key-you-defined-in-your-dotenv"

     curl -X GET "https://a635-58-96-38-129.ngrok-free.app/confetti" \
     -H "X-API-Key: the-api-key-you-defined-in-your-dotenv"

    ```

## Usage
- Gavin exposes various automation endpoints that can be triggered through Raycast
- The AI agent processes requests and returns snarky but helpful responses
- All endpoints are secured and require proper authentication

## Development
- The project uses FastAPI for the backend
- Playwright for browser automation
- Pydantic for data validation
- Uvicorn as the ASGI server

