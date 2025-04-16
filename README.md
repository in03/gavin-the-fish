# Gavin-The-Fish
**Gavin the Fish** is a snarky Siri style assistant proof of concept. 

Gavin utilises a tool bridge to expose local scripts, MCP servers and more to 11 Labs Conversational AI for tool calling.

> [!Warning] 
> 🚧 Work in progress! Just testing some cheeky tricks!

## Setup
1. Clone the repository
2. Install Python 3.13 or higher
3. Install dependencies:
   ```bash
   uv sync
   ```
4. Set up your environment variables in `.env`:
   - Define whatever you like as your API key. Recommend a UUID.

## Installation
1. Install the Raycast extension
2. Configure your agent
3. Start the FastAPI server:
   ```bash
   uv run run_server.py
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
- Careful of trailing slashes on your endpoints! They will cause 307 errors.

## Development
- The project uses FastAPI for the backend
- Playwright for browser automation
- Pydantic for data validation
- Uvicorn as the ASGI server

## Job Management System

### Overview
The job management system provides a way to handle long-running tasks in a way that's friendly for LLM integration. It allows for:
- Starting background jobs
- Tracking job status
- Getting human-readable status updates
- Cancelling running jobs

### Current Implementation
- In-memory job registry
- Basic job lifecycle (pending, running, success, failed, cancelled, expired)
- Human-readable status messages
- Unified job status endpoint
- Integration with existing tools (Fibonacci, Goose)

### Roadmap

#### Phase 1: Job Management
- [x] In-memory job registry
- [x] Basic job lifecycle states
- [x] Human-readable status messages
- [x] Unified job status endpoint
- [x] Integration with existing tools
- [ ] Automatic convert blocking tasks to jobs after timeout
- [ ] Handle job failure due to timeouts
- [x] Native job status notifications

#### Phase 2: MCP Integration via MCP Bridge
- [ ] Implement BYO client support (Goose, Claude)
- [ ] Implement server management

#### Phase 3: Frontend
- [ ] Native GUI integration (Tauri, Electron, rumps)
- [ ] Assistant-style UX, wakeword trigger and minimal UI
- [ ] Standard chat UX, transcript, text entry and voice chat

### Design Principles
1. **LLM-Friendly**: Status messages and responses are designed to be easily understood by LLMs
2. **Simple Interface**: Minimal endpoints with clear, consistent responses
3. **Extensible**: Easy to add new job types and features
4. **Reliable**: Robust error handling and status tracking
5. **Maintainable**: Clean code structure with clear separation of concerns

### Example Usage
```bash
# Start a job
curl -X POST http://localhost:8000/fibonacci \
  -H "Content-Type: application/json" \
  -d '{"n": 100}'

# List all jobs
curl http://localhost:8000/jobs

# Get specific job status
curl http://localhost:8000/jobs/{job_id}

# Cancel a job
curl -X POST http://localhost:8000/jobs/{job_id}/cancel
```

## Roadmap

