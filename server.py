#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
College Football GraphQL MCP Server

A comprehensive GraphQL wrapper for college football data with schema introspection,
caching, security validation, and MCP protocol support.
"""

import json
import logging
import time
from dotenv import load_dotenv

from fastmcp import Context
from pydantic import ValidationError

# Load environment variables from .env file
load_dotenv()

# Import our organized modules
from src.models import QueryInput, GraphQLError
from src.server_state import ServerState
from src.async_utils import generate_request_id
from src.graphql_executor import set_server_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the shared MCP server instance and initialize global state
from src.mcp_server import mcp
server_state = ServerState()

# Initialize server state for GraphQL executor immediately
set_server_state(server_state)

# Import tool modules to register their @mcp.tool decorators
# This must come AFTER setting server_state so tools have access to it
import tools  # noqa: F401 - Import needed for side effects (registers MCP tools)


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
async def execute_query(query_input: QueryInput, ctx: Context) -> str:
    """
    Execute a GraphQL query against the college football database.
    Includes automatic query validation and security checks.
    
    Args:
        query_input: GraphQL query with optional variables and operation name
    
    Returns:
        JSON string containing the query results
    """
    request_id = generate_request_id()
    
    try:
        await ctx.info(f"[{request_id}] Executing GraphQL query: {query_input.operation_name or 'unnamed'}")
        
        # Ensure server is initialized
        if not server_state.initialized:
            await server_state.initialize()
        
        # Rate limiting check
        if not server_state.check_rate_limit():
            raise GraphQLError("Rate limit exceeded")
        
        # Check cache first
        cache_key = server_state.get_cache_key(query_input.query, query_input.variables)
        cached_result = server_state.query_cache.get(cache_key)
        if cached_result is not None:
            await ctx.debug(f"[{request_id}] Cache hit")
            return json.dumps(cached_result, indent=2)
        
        # Execute query
        start_time = time.time()
        result = await server_state.graphql_client.execute_query(
            query_input.query,
            query_input.variables,
            ctx
        )
        execution_time = time.time() - start_time
        
        # Cache successful result
        server_state.query_cache.set(cache_key, result)
        
        # Update stats
        server_state.request_count += 1
        await ctx.info(f"[{request_id}] Query executed successfully in {execution_time:.3f}s (total requests: {server_state.request_count})")
        
        return json.dumps(result, indent=2)
    
    except ValidationError as e:
        await ctx.error(f"[{request_id}] Validation error: {e}")
        return json.dumps({"error": "Invalid input", "details": str(e), "request_id": request_id})
    
    except GraphQLError as e:
        await ctx.error(f"[{request_id}] GraphQL error: {e}")
        return json.dumps({"error": str(e), "request_id": request_id, "query": e.query[:100] if e.query else None})
    
    except Exception as e:
        await ctx.error(f"[{request_id}] Unexpected error: {e}")
        return json.dumps({"error": f"Unexpected error: {str(e)}", "request_id": request_id})


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info("Starting College Football GraphQL MCP Server with HTTP transport...")
    logger.info("Server will be available at http://127.0.0.1:8345/mcp")
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8345)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise