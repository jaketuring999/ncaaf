# NCAAF MCP API Middleware

FastAPI middleware that provides streaming responses from the NCAAF MCP server using OpenAI Agents SDK.

## Overview

This middleware acts as a bridge between clients and the NCAAF MCP server, providing:
- Streaming responses via Server-Sent Events (SSE)
- OpenAI Agents SDK integration for conversational AI
- Authentication and request management
- Usage logging and analytics
- Health monitoring

## Architecture

```
Client → Middleware (FastAPI) → NCAAF MCP Server (FastMCP)
```

The middleware receives natural language queries, processes them through an OpenAI Agent with access to NCAAF MCP tools, and streams the results back to the client in real-time.

## Configuration

### Environment Variables

All configuration uses the `NCAAF_API_` prefix:

```bash
# Server Configuration
NCAAF_API_HOST=0.0.0.0
NCAAF_API_PORT=8346
NCAAF_API_DEBUG=false

# MCP Server
NCAAF_API_MCP_SERVER_URL=http://localhost:8345

# Authentication
NCAAF_API_REQUIRE_AUTH=true
NCAAF_API_AUTH_USERNAME=your_username
NCAAF_API_AUTH_PASSWORD=your_password

# OpenAI
NCAAF_API_OPENAI_MODEL=gpt-5-mini

# Database (Optional - for usage logging)
POSTGRES_URL_USAGE=postgresql://user:pass@host:port/db
```

## Installation & Usage

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the NCAAF MCP server (port 8345):
```bash
cd /path/to/ncaaf
git ls-files | entr -r fastmcp run server.py --transport http --port 8345
```

3. Start the middleware:
```bash
cd middleware
python app/main.py
```

### Docker

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

## API Endpoints

### POST /api/query/stream

Stream NCAAF analytics queries with Server-Sent Events.

**Request:**
```json
{
  "query": "How has Alabama performed against ranked opponents this season?",
  "previous_response_id": "optional-conversation-id"
}
```

**Response:** SSE stream with events:
- `stream.started`: Query processing begins
- `response.tool.started`: MCP tool execution begins  
- `response.tool.completed`: MCP tool execution complete
- `response.text.delta`: Streaming response text
- `stream.completed`: Query processing complete

### GET /api/health

Health check endpoint that verifies MCP server connectivity.

## Features

### Streaming Responses
Real-time streaming of AI responses using Server-Sent Events, providing immediate feedback as tools execute and responses generate.

### OpenAI Agents Integration  
Uses the OpenAI Agents SDK to create conversational experiences with access to NCAAF MCP tools for comprehensive college football analysis.

### Authentication
HTTP Basic Authentication with configurable credentials. Can be disabled for development.

### Usage Logging
Optional PostgreSQL-based usage logging that tracks:
- Query details and responses
- Token usage and costs
- Tool execution metrics  
- Performance analytics

### Error Handling
Comprehensive error handling with graceful degradation, circuit breakers for external services, and detailed logging.

## MCP Tools Available

The middleware provides access to all NCAAF MCP tools:

- **Team Analysis:** Statistics, records, conference performance
- **Game Data:** Schedules, results, betting lines
- **Player Data:** Statistics, recruiting, transfers  
- **Rankings:** Polls, computer rankings, CFP standings
- **Betting Analytics:** Historical outcomes, line analysis
- **GraphQL:** Direct database queries and schema exploration

## System Prompt

The middleware uses a specialized system prompt for college football analysis located at:
`/Users/Jake/PycharmProjects/mcp-spider/prompts/ncaaf-systemprompt-v1.md`

This prompt configures the AI agent to:
- Focus on college football specific factors
- Provide betting analysis using the CollegeBetSmarter framework
- Consider unique NCAAF dynamics (recruiting, conferences, transfers)
- Deliver professional, data-driven insights

## Development

### Project Structure
```
middleware/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── auth.py              # Authentication  
│   ├── api/
│   │   └── query.py         # API endpoints
│   ├── services/
│   │   ├── agent_service.py # OpenAI Agent management
│   │   ├── streaming_service.py # SSE streaming
│   │   └── logging_service.py   # Usage logging
│   └── db/
│       └── connection.py    # Database connections
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### Key Components

- **AgentService:** Manages OpenAI Agent lifecycle and MCP server connections
- **StreamingService:** Processes queries and streams SSE responses  
- **LoggingService:** Non-blocking usage analytics with circuit breakers
- **AuthService:** HTTP Basic Authentication with constant-time comparisons

## Monitoring & Observability

- Health checks at `/api/health`
- Structured logging with configurable levels
- Usage metrics and token tracking
- Error tracking and circuit breakers
- Docker health checks and restart policies

## Scaling Considerations

- Configurable concurrent request limits
- Connection pooling for database operations
- Async/await throughout for high concurrency
- Graceful degradation when external services unavailable
- Efficient memory usage with streaming responses

## Security

- HTTP Basic Authentication with secure credential comparison
- CORS middleware with configurable origins
- Non-root Docker user
- Environment variable based configuration
- Optional database logging (no sensitive data exposure)

## License

This middleware implementation is based on the NFL MCP middleware pattern and adapted for NCAAF use cases.