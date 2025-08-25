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
from typing import Optional
from dotenv import load_dotenv

from fastmcp import FastMCP, Context
from pydantic import ValidationError

# Load environment variables from .env file
load_dotenv()

# Import our organized modules
from src.models import QueryInput, GraphQLError
from src.server_state import ServerState
from src.graphql import format_graphql_type, validate_basic_query_syntax
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
import tools


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
async def execute_query(query_input: QueryInput, ctx: Context) -> str:
    """
    Execute a GraphQL query against the college football database.
    
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


@mcp.tool()
async def introspect_schema(ctx: Context) -> str:
    """
    Introspect the GraphQL schema to discover available types, queries, and mutations.
    
    Returns:
        JSON string containing the schema structure
    """
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          ...FullType
        }
        directives {
          name
          description
          locations
          args {
            ...InputValue
          }
        }
      }
    }
    
    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          ...InputValue
        }
        type {
          ...TypeRef
        }
        isDeprecated
        deprecationReason
      }
      inputFields {
        ...InputValue
      }
      interfaces {
        ...TypeRef
      }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        ...TypeRef
      }
    }
    
    fragment InputValue on __InputValue {
      name
      description
      type { ...TypeRef }
      defaultValue
    }
    
    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    try:
        await ctx.info("Performing schema introspection...")
        
        # Check cache first
        cached_schema = server_state.schema_cache.get("schema")
        if cached_schema:
            await ctx.info("Using cached schema")
            return json.dumps(cached_schema, indent=2)
        
        # Execute introspection
        result = await server_state.graphql_client.execute_query(introspection_query, {}, ctx)
        server_state.schema_cache.set("schema", result, ttl=3600)  # Cache for 1 hour
        
        await ctx.info("Schema introspection completed")
        return json.dumps(result, indent=2)
    
    except Exception as e:
        await ctx.error(f"Schema introspection failed: {e}")
        return json.dumps({"error": f"Schema introspection failed: {e}"})


@mcp.tool()
async def get_schema_types(filter_kind: Optional[str] = None, ctx: Context = None) -> str:
    """
    Get available GraphQL types from the schema.
    
    Args:
        filter_kind: Filter by type kind (OBJECT, SCALAR, ENUM, etc.)
    
    Returns:
        JSON string containing filtered schema types
    """
    try:
        # Get cached schema
        cached_schema = server_state.schema_cache.get("schema")
        if not cached_schema:
            await ctx.info("Schema not cached, performing introspection...")
            await introspect_schema(ctx)
            cached_schema = server_state.schema_cache.get("schema")
        
        schema = cached_schema.get("data", {}).get("__schema", {})
        types = schema.get("types", [])
        
        if filter_kind:
            types = [t for t in types if t.get("kind") == filter_kind.upper()]
        
        # Filter out built-in types
        types = [t for t in types if not t.get("name", "").startswith("__")]
        
        result = {
            "types": types,
            "count": len(types),
            "filter": filter_kind
        }
        
        await ctx.info(f"Retrieved {len(types)} schema types")
        return json.dumps(result, indent=2)
    
    except Exception as e:
        await ctx.error(f"Failed to get schema types: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_query_fields(ctx: Context) -> str:
    """
    Get available query fields from the schema.
    
    Returns:
        JSON string containing query fields and their arguments
    """
    try:
        # Get cached schema
        cached_schema = server_state.schema_cache.get("schema")
        if not cached_schema:
            await introspect_schema(ctx)
            cached_schema = server_state.schema_cache.get("schema")
        
        schema = cached_schema.get("data", {}).get("__schema", {})
        query_type_name = schema.get("queryType", {}).get("name")
        
        if not query_type_name:
            return json.dumps({"error": "No query type found in schema"})
        
        types = schema.get("types", [])
        query_type = next((t for t in types if t.get("name") == query_type_name), None)
        
        if not query_type:
            return json.dumps({"error": f"Query type '{query_type_name}' not found"})
        
        fields = query_type.get("fields", [])
        
        # Format fields for easy consumption
        formatted_fields = []
        for field in fields:
            formatted_field = {
                "name": field.get("name"),
                "description": field.get("description"),
                "type": format_graphql_type(field.get("type", {})),
                "args": [
                    {
                        "name": arg.get("name"),
                        "type": format_graphql_type(arg.get("type", {})),
                        "description": arg.get("description"),
                        "defaultValue": arg.get("defaultValue")
                    }
                    for arg in field.get("args", [])
                ]
            }
            formatted_fields.append(formatted_field)
        
        result = {
            "queryType": query_type_name,
            "fields": formatted_fields,
            "count": len(formatted_fields)
        }
        
        await ctx.info(f"Retrieved {len(formatted_fields)} query fields")
        return json.dumps(result, indent=2)
    
    except Exception as e:
        await ctx.error(f"Failed to get query fields: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def validate_query(query: str, ctx: Context) -> str:
    """
    Validate a GraphQL query without executing it.
    
    Args:
        query: GraphQL query string to validate
    
    Returns:
        JSON string containing validation results
    """
    try:
        await ctx.info("Validating GraphQL query...")
        
        # Basic syntax validation
        result = validate_basic_query_syntax(query)
        
        if result["valid"]:
            await ctx.info("Query validation passed")
        else:
            await ctx.error(f"Query validation failed: {result['errors']}")
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        await ctx.error(f"Query validation failed: {e}")
        return json.dumps({"error": str(e)})



# =============================================================================
# MCP Resources
# =============================================================================

@mcp.resource("config://server")
async def get_server_config() -> str:
    """Get current server configuration"""
    return json.dumps(server_state.get_masked_config(), indent=2)


@mcp.resource("schema://types")
async def get_cached_schema() -> str:
    """Get cached schema information"""
    cached_schema = server_state.schema_cache.get("schema")
    if cached_schema:
        return json.dumps(cached_schema, indent=2)
    return json.dumps({"error": "Schema not cached"})


# =============================================================================
# MCP Prompts
# =============================================================================

@mcp.prompt()
def generate_query_prompt(entity_type: str, fields: str = None) -> str:
    """Generate a prompt for creating GraphQL queries"""
    base_prompt = f"""Generate a GraphQL query for {entity_type} data from a college football database.

The query should:
1. Request relevant fields for {entity_type}
2. Include appropriate filters and arguments
3. Be well-structured and efficient
4. Include comments explaining the query purpose

"""
    
    if fields:
        base_prompt += f"Focus on these specific fields: {fields}\n\n"
    
    base_prompt += """Example query structure:
query GetData($filter: FilterInput) {
  entityName(filter: $filter) {
    id
    name
    # other relevant fields
  }
}

Please provide a complete GraphQL query with variables if needed."""
    
    return base_prompt


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