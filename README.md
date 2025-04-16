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

## Design Principles
1. **LLM-Friendly**: Status messages and responses are designed to be easily understood by LLMs
2. **Simple Interface**: Minimal endpoints with clear, consistent responses
3. **Extensible**: Easy to add new job types and features
4. **Reliable**: Robust error handling and status tracking
5. **Maintainable**: Clean code structure with clear separation of concerns

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

### Phase 1: Job Management
- [x] In-memory job registry
- [x] Basic job lifecycle states
- [x] Human-readable status messages
- [x] Unified job status endpoint
- [x] Integration with existing tools
- [ ] Automatic convert blocking tasks to jobs after timeout
- [ ] Handle job failure due to timeouts
- [x] Native job status notifications

### Phase 2: MCP Integration via MCP Bridge
- [ ] Implement BYO client support (Goose, Claude)
- [ ] Implement server management

### Phase 3: Frontend
- [ ] Native GUI integration (Tauri, Electron, rumps)
- [ ] Assistant-style UX, wakeword trigger and minimal UI
- [ ] Standard chat UX, transcript, text entry and voice chat

## 🧠 Braindump

### MCP Bridging

There are three possible implementations of an MCP bridge that I can see here:

1. Unified tool router
2. Tool sync via API
3. Custom LiveKit

#### Unified Tool Router
Doing the unified tool router makes things very simple implementation wise. 
- Install as many MCP tools as needed.
- Agent always calls the same tool with the same endpoint using a natural language query.

Something like this:

**Request**
```shell
curl -X POST http://localhost:8000/execute_mcp_tool \
  -H "Content-Type: application/json" \
  -d '{"query": "Send an email to Darryl and tell him I'\''m working really hard."}'
```

**Response**
```json
{
  "status": "success", 
  "result": {
    "tool_name": "send_email",
    "action": "send",
    "recipient": "Darryl",
    "subject": "Work Update",
    "body": "Hi Darryl,\n\nI wanted to let you know that I'm working really hard.\n\nBest regards",
    "metadata": {
      "sent_at": "2024-01-20T15:30:00Z",
      "message_id": "msg_123abc",
      "conversation_id": "conv_456def"
    }
  },
  "error": null,
  "job_id": "job_789ghi",
  "status_message": "Email sent successfully to Darryl"
}
```

#### Tool Sync via API
If we grant access to the server to control the ConvAI agent configuration via API, we can reimplement MCP tools as native ElevenLabs agent tools.

This would require parsing the MCP schema and translating to 11L agent tools schema. We would also need to keep this in sync by iterating MCP servers' tools and pushing the tools to the agent. This sync logic could get a bit hairy in some scenarios. Tools would also be implemented in a flat structure, while possible to keep alphabetical and organised in the json, it won't be much fun to look at in the dashboard. Additional controls for managing tools may be necessary.

The OpenAI tool JSON Schema that ElevenLabs agents use is actually very similar to MCP. But there will likely be cases where the translation isn't so straightforward or may be unsupported:

- **Nested tools:** RPC namespaces for nested or hierarchical tools will need to be flattened.
- **Dynamic params:** Some tools dynamically alter param schema at runtime based on previous context. Implement a custom tool to fetch schema at runtime?
- **Stateful tools:** Tools that depend on prior tool calls – may be able to mitigate with job management.
- **Non schema compatible inputs:** Tools that accept `any`, polymorphic input or deeply nested structures may not validate on parse.
- **Streamed output:** Agent expects a single structured response from a webhook. If the tool streams logs or progress, we'd need to handle as a job.

Some of the above will apply to the Unified tool too.

#### LiveKit Implementation
Forego ConvAI, create a LiveKit agent and use 11L TTS and STT.

This would allow us to implement fully native MCP and control the way the agent responds to long running jobs in a more natural way.

It also means completely reinventing much of the wheel and being subject to LiveKit's pricing structure. A bit too much work for an experiment...






