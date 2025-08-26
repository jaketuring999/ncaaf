# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a College Football GraphQL MCP (Model Context Protocol) Server built with FastMCP 2.0. The server provides structured access to NCAA football data through both GraphQL queries and specialized MCP tools.

## Architecture

### Core Components
- **MCP Instance**: Single global FastMCP instance (`mcp_instance.py`) shared across all tools
- **GraphQL Layer**: Query execution and response formatting (`src/graphql_executor.py`, `src/graphql.py`)
- **Tool Categories**: Organized in `tools/` directory by domain (teams, games, betting, rankings, athletes, metrics, schema)
- **Utilities**: Response formatting, parameter processing, and domain-specific helpers in `utils/`

### Key Files
- `server.py`: Main entry point with MCP tool registration
- `src/models.py`: Pydantic models for validation
- `cfbd-schema.graphql`: GraphQL schema definition
- `tools/__init__.py`: Auto-imports all tool modules to register @mcp.tool decorators

## Development Commands

### Running the Server
```bash
python server.py
```

### FastMCP Commands
```bash
fastmcp run server.py  # Alternative way to run
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Code Patterns

### MCP Tool Registration
Tools are automatically registered via the shared MCP instance:
```python
from mcp_instance import mcp

@mcp.tool()
async def tool_name(param: str) -> str:
    """Tool description"""
    # Implementation
```

### Parameter Handling
- String/int parameters are handled flexibly (e.g., `Union[str, int]`)
- Boolean parameters accept string representations (`"true"`, `"false"`, etc.)
- Team identification supports name, abbreviation, or ID

### Response Formatting
- Default output is YAML-formatted for readability
- `include_raw_data` parameter controls JSON vs formatted output
- Response formatter (`utils/response_formatter.py`) handles query-type-specific formatting

### GraphQL Integration
- Direct GraphQL execution via `execute_query` tool
- Query type detection for appropriate response formatting
- Enhanced error handling with suggestions and context

## Domain Structure

**Teams**: Team lookup, search, conference filtering
**Games**: Game data by week, team, season with optional betting/weather data
**Rankings**: College football poll rankings by week/season
**Betting**: Lines, analysis, and betting performance metrics
**Athletes**: Player rosters and statistics
**Metrics**: Advanced team performance analytics
**Schema**: GraphQL schema exploration and introspection

# run fast mcp server with git ls-files | entr -r fastmcp run server.py --transport http --port 8345