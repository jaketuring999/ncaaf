#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
College Football GraphQL MCP Server

A simple GraphQL wrapper for college football data with MCP protocol support.
"""

import json
import logging
from dotenv import load_dotenv

from fastmcp import Context
from pydantic import ValidationError

# Load environment variables from .env file
load_dotenv()

# Import our modules
from src.models import QueryInput, GraphQLError
from src.graphql_executor import execute_graphql, cleanup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the shared MCP instance
from mcp_instance import mcp

# Import tools to register with MCP instance  
import tools


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
    try:
        await ctx.info(f"Executing GraphQL query: {query_input.operation_name or 'unnamed'}")
        
        result = await execute_graphql(
            query_input.query,
            query_input.variables,
            ctx
        )
        
        await ctx.info("Query executed successfully")
        return result
    
    except ValidationError as e:
        await ctx.error(f"Validation error: {e}")
        return json.dumps({"error": "Invalid input", "details": str(e)})
    
    except GraphQLError as e:
        await ctx.error(f"GraphQL error: {e}")
        return json.dumps({"error": str(e), "query": e.query[:100] if e.query else None})
    
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


# =============================================================================
# Cleanup
# =============================================================================

async def server_cleanup():
    """Clean up server resources."""
    await cleanup()


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info("Starting College Football GraphQL MCP Server...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise