#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
College Football GraphQL MCP Server

A simple GraphQL wrapper for college football data with MCP protocol support.
"""

import json
import logging
from typing import Union, Optional, Dict, Any
from dotenv import load_dotenv

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

# GraphQL query execution tool
@mcp.tool()
async def execute_query(
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    operation_name: Optional[str] = None
) -> str:
    """
    Execute a GraphQL query against the college football database.
    Alternative version with individual parameters instead of a model.
    
    Args:
        query: GraphQL query string
        variables: Query variables dictionary
        operation_name: Operation name (optional)
    
    Returns:
        JSON string containing the query results
    """
    try:
        # Validate using QueryInput model internally
        query_input = QueryInput(
            query=query,
            variables=variables or {},
            operation_name=operation_name
        )
        
        result = await execute_graphql(
            query_input.query,
            query_input.variables
        )
        
        return result
    
    except ValidationError as e:
        return json.dumps({"error": "Invalid input", "details": str(e)})
    
    except GraphQLError as e:
        return json.dumps({"error": str(e), "query": e.query[:100] if e.query else None})
    
    except Exception as e:
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