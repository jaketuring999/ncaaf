"""
Simple GraphQL execution utilities for MCP tools.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

import httpx
from fastmcp import Context

from .models import GraphQLError
from .graphql import GraphQLClient

logger = logging.getLogger(__name__)

# Simple global HTTP client
_http_client: Optional[httpx.AsyncClient] = None
_graphql_client: Optional[GraphQLClient] = None


async def get_graphql_client() -> GraphQLClient:
    """Get or create the GraphQL client."""
    global _http_client, _graphql_client
    
    if _graphql_client is None:
        # Get API configuration from environment
        api_key = os.getenv("CFBD_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Set CFBD_API_KEY environment variable.")
        
        endpoint = os.getenv("CFBD_ENDPOINT", "https://graphql.collegefootballdata.com/v1/graphql")
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Create HTTP client if needed
        if _http_client is None:
            _http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=20)
            )
        
        _graphql_client = GraphQLClient(
            http_client=_http_client,
            endpoint=endpoint,
            headers=headers
        )
    
    return _graphql_client


async def execute_graphql(query: str, variables: Dict[str, Any] = None, ctx: Context = None) -> str:
    """
    Execute a GraphQL query.
    
    Args:
        query: GraphQL query string
        variables: Query variables dictionary
        ctx: MCP context for logging
    
    Returns:
        JSON string containing the query results
    
    Raises:
        GraphQLError: If query execution fails
    """
    variables = variables or {}
    
    try:
        if ctx:
            await ctx.info(f"Executing GraphQL query with {len(variables)} variables")
        
        client = await get_graphql_client()
        result = await client.execute_query(query, variables, ctx)
        
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


async def cleanup():
    """Clean up HTTP client resources."""
    global _http_client, _graphql_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
        _graphql_client = None