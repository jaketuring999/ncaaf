"""
Shared GraphQL execution utilities for MCP tools.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastmcp import Context

from .models import GraphQLError
from .server_state import ServerState

logger = logging.getLogger(__name__)

# Global reference to server state - will be set in server.py
server_state: Optional[ServerState] = None

def set_server_state(state: ServerState):
    """Set the global server state reference."""
    global server_state
    server_state = state

async def execute_graphql(query: str, variables: Dict[str, Any] = None, ctx: Context = None) -> str:
    """
    Execute a GraphQL query using the shared server infrastructure.
    
    Args:
        query: GraphQL query string
        variables: Query variables dictionary
        ctx: MCP context for logging
    
    Returns:
        JSON string containing the query results
    
    Raises:
        GraphQLError: If query execution fails
    """
    if not server_state:
        raise GraphQLError("Server state not initialized")
    
    variables = variables or {}
    
    try:
        if ctx:
            await ctx.info(f"Executing GraphQL query with {len(variables)} variables")
        
        # Ensure server is initialized
        if not server_state.initialized:
            await server_state.initialize()
        
        # Rate limiting check
        if not server_state.check_rate_limit():
            raise GraphQLError("Rate limit exceeded")
        
        # Check cache first
        cache_key = server_state.get_cache_key(query, variables)
        cached_result = server_state.query_cache.get(cache_key)
        if cached_result is not None:
            if ctx:
                await ctx.debug("Cache hit")
            return json.dumps(cached_result, indent=2)
        
        # Execute query
        result = await server_state.graphql_client.execute_query(
            query,
            variables,
            ctx
        )
        
        # Cache successful result
        server_state.query_cache.set(cache_key, result)
        
        # Update stats
        server_state.request_count += 1
        if ctx:
            await ctx.info(f"Query executed successfully (total requests: {server_state.request_count})")
        
        return json.dumps(result, indent=2)
    
    except GraphQLError:
        # Re-raise GraphQL errors as-is
        raise
    except Exception as e:
        error_msg = f"Unexpected error executing GraphQL query: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise GraphQLError(error_msg)

def build_query_variables(**kwargs) -> Dict[str, Any]:
    """
    Build GraphQL variables dict, filtering out None values.
    
    Args:
        **kwargs: Named parameters to include as variables
    
    Returns:
        Dict with non-None values
    """
    return {key: value for key, value in kwargs.items() if value is not None}