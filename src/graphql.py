"""
GraphQL execution and utilities for the NCAAF MCP Server.
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional

import httpx
from fastmcp import Context

from .models import GraphQLError
from .security import SecurityValidator

logger = logging.getLogger(__name__)


class GraphQLClient:
    """GraphQL client with retry logic and error handling"""
    
    def __init__(self, http_client: httpx.AsyncClient, endpoint: str, headers: Dict[str, str], 
                 max_retries: int = 3):
        self.http_client = http_client
        self.endpoint = endpoint
        self.headers = headers
        self.max_retries = max_retries
    
    async def execute_query(self, query: str, variables: Dict[str, Any] = None, 
                          ctx: Context = None) -> Dict[str, Any]:
        """
        Execute GraphQL query with enhanced error handling and retry logic.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            ctx: MCP context for logging
            
        Returns:
            GraphQL response data
            
        Raises:
            GraphQLError: If query execution fails
        """
        variables = variables or {}
        
        # Security validation
        is_valid, error_msg = SecurityValidator.validate_query(query)
        if not is_valid:
            if ctx:
                await ctx.error(f"Security validation failed: {error_msg}")
            raise GraphQLError(f"Query rejected: {error_msg}", query=query)
        
        # Prepare request
        payload = {
            "query": query,
            "variables": variables
        }
        
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(self.headers)
        
        # Execute with enhanced retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if ctx:
                    await ctx.debug(f"Executing GraphQL query (attempt {attempt + 1}/{self.max_retries})")
                
                response = await self.http_client.post(
                    self.endpoint,
                    json=payload,
                    headers=request_headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check for GraphQL errors
                    if result.get("errors"):
                        error_msg = "; ".join([err.get("message", "Unknown error") for err in result["errors"]])
                        raise GraphQLError(f"GraphQL errors: {error_msg}", query=query)
                    
                    if ctx:
                        await ctx.debug("Query executed successfully")
                    
                    return result
                else:
                    raise GraphQLError(f"HTTP {response.status_code}: {response.text if hasattr(response, 'text') else 'Unknown error'}", 
                                     query=query, status_code=response.status_code)
            
            except httpx.TimeoutException as e:
                last_error = GraphQLError(f"Query timeout: {str(e)}", query=query)
                if ctx:
                    await ctx.error(f"Query timeout on attempt {attempt + 1}")
            
            except httpx.HTTPStatusError as e:
                last_error = GraphQLError(f"HTTP {e.response.status_code}: {e.response.text if hasattr(e.response, 'text') else 'Unknown error'}", 
                                        query=query, status_code=e.response.status_code)
                if ctx:
                    await ctx.error(f"HTTP error on attempt {attempt + 1}: {e.response.status_code}")
                
                # Don't retry on client errors (4xx)
                if e.response.status_code < 500:
                    break
            
            except Exception as e:
                last_error = GraphQLError(f"Query execution failed: {str(e)}", query=query)
                if ctx:
                    await ctx.error(f"Query attempt {attempt + 1} failed: {e}")
            
            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                backoff_time = min(2 ** attempt, 60)  # Cap at 60 seconds
                if ctx:
                    await ctx.debug(f"Retrying in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
        
        if ctx:
            await ctx.error(f"All {self.max_retries} retry attempts failed")
        raise last_error


def format_graphql_type(type_obj: Dict) -> str:
    """
    Helper function to format GraphQL type information.
    
    Args:
        type_obj: GraphQL type object from introspection
        
    Returns:
        Formatted type string
    """
    if not type_obj:
        return "Unknown"
    
    kind = type_obj.get("kind")
    name = type_obj.get("name")
    of_type = type_obj.get("ofType")
    
    if kind == "NON_NULL":
        return f"{format_graphql_type(of_type)}!"
    elif kind == "LIST":
        return f"[{format_graphql_type(of_type)}]"
    elif name:
        return name
    elif of_type:
        return format_graphql_type(of_type)
    else:
        return "Unknown"


def generate_cache_key(query: str, variables: Dict[str, Any]) -> str:
    """
    Generate a consistent cache key for a GraphQL query.
    
    Args:
        query: GraphQL query string
        variables: Query variables
        
    Returns:
        Cache key string
    """
    return f"{hash(query)}_{hash(str(sorted(variables.items())))}"


def validate_basic_query_syntax(query: str) -> Dict[str, Any]:
    """
    Perform basic GraphQL query syntax validation.
    
    Args:
        query: GraphQL query string to validate
        
    Returns:
        Validation result dictionary
    """
    validation_errors = []
    
    if not query.strip():
        validation_errors.append("Query is empty")
    
    if "{" not in query or "}" not in query:
        validation_errors.append("Query appears to be malformed (missing braces)")
    
    # Check for balanced braces
    brace_count = query.count("{") - query.count("}")
    if brace_count != 0:
        validation_errors.append(f"Unbalanced braces (difference: {brace_count})")
    
    return {
        "valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "query_length": len(query),
        "estimated_complexity": query.count("{") + query.count("(")
    }