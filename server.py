#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
College Football GraphQL MCP Server

A simple GraphQL wrapper for college football data with MCP protocol support.
"""

import json
import logging
import re
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
# Helper Functions
# =============================================================================

def detect_graphql_query_type(query: str) -> str:
    """
    Detect the type of GraphQL query to determine appropriate formatting.
    
    Args:
        query: GraphQL query string
        
    Returns:
        String indicating the detected query type (teams, games, betting, etc.)
    """
    query_lower = query.lower().strip()
    
    # Remove comments and normalize whitespace
    query_cleaned = re.sub(r'#.*$', '', query_lower, flags=re.MULTILINE)
    query_cleaned = re.sub(r'\s+', ' ', query_cleaned).strip()
    
    # Check for specific entity types in the query
    if re.search(r'\bcurrentteams\b|\bteam\b.*\bschool\b|\bteamid\b', query_cleaned):
        return 'teams'
    elif re.search(r'\bgame\b.*\b(hometeam|awayteam|homepoints|awaypoints)\b|\bgamebyweek\b', query_cleaned):
        return 'games'
    elif re.search(r'\blines\b|\bbetting\b|\bspread\b|\boverunder\b', query_cleaned):
        return 'betting'
    elif re.search(r'\bpoll\b|\brankings\b|\brank\b', query_cleaned):
        return 'rankings'
    elif re.search(r'\bathlete\b|\bplayer\b|\bposition\b', query_cleaned):
        return 'athletes'
    elif re.search(r'\bmetrics\b|\badvanced\b|\bstats\b', query_cleaned):
        return 'metrics'
    else:
        # Default to generic formatting
        return 'generic'


# =============================================================================
# MCP Tools
# =============================================================================

# GraphQL query execution tool
@mcp.tool()
async def execute_query(
    query: str,
    variables: Optional[str] = None,
    operation_name: Optional[str] = None,
    include_raw_data: Union[str, bool] = False
) -> str:
    """
    Execute a GraphQL query against the college football database.
    Alternative version with individual parameters instead of a model.
    
    Args:
        query: GraphQL query string
        variables: Query variables as JSON string (optional)
        operation_name: Operation name (optional)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        YAML formatted response containing the query results
    """
    try:
        # Parse variables from JSON string
        parsed_variables = {}
        if variables:
            try:
                parsed_variables = json.loads(variables)
                if not isinstance(parsed_variables, dict):
                    return json.dumps({
                        "error": "Variables must be a JSON object",
                        "provided": variables
                    })
            except json.JSONDecodeError as e:
                return json.dumps({
                    "error": "Invalid JSON in variables parameter",
                    "details": str(e),
                    "provided": variables
                })
        
        # Convert include_raw_data to boolean
        include_raw_data_bool = False
        if isinstance(include_raw_data, str):
            include_raw_data_bool = include_raw_data.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(include_raw_data, bool):
            include_raw_data_bool = include_raw_data
        
        # Validate using QueryInput model internally
        query_input = QueryInput(
            query=query,
            variables=parsed_variables,
            operation_name=operation_name
        )
        
        result = await execute_graphql(
            query_input.query,
            query_input.variables
        )
        
        # Apply formatting based on include_raw_data flag
        if include_raw_data_bool:
            return result
        else:
            # Import here to avoid circular imports
            from utils.response_formatter import safe_format_response
            # Detect query type and format appropriately
            query_type = detect_graphql_query_type(query)
            return safe_format_response(result, query_type, include_raw_data_bool)
    
    except ValidationError as e:
        # Better error formatting using YAML
        error_response = {
            "error": "Query validation failed",
            "details": str(e),
            "query_preview": query[:100] + "..." if len(query) > 100 else query,
            "suggestions": [
                "Check query syntax for GraphQL compliance",
                "Ensure all required fields are included",
                "Verify field names match the schema"
            ]
        }
        # Import here to avoid circular imports
        from utils.response_formatter import optimize_for_yaml
        import yaml
        return yaml.dump(optimize_for_yaml(error_response), default_flow_style=False)
    
    except GraphQLError as e:
        # Enhanced GraphQL error handling
        error_response = {
            "error": "GraphQL execution failed",
            "details": str(e),
            "query_preview": e.query[:100] + "..." if e.query and len(e.query) > 100 else e.query,
            "status_code": e.status_code if hasattr(e, 'status_code') and e.status_code else None,
            "suggestions": [
                "Check if the queried fields exist in the schema",
                "Verify authentication and permissions",
                "Try with a simpler query structure"
            ]
        }
        # Import here to avoid circular imports  
        from utils.response_formatter import optimize_for_yaml
        import yaml
        return yaml.dump(optimize_for_yaml(error_response), default_flow_style=False)
    
    except Exception as e:
        # Generic error handling with helpful context
        error_response = {
            "error": "Unexpected error occurred",
            "details": str(e),
            "error_type": type(e).__name__,
            "query_preview": query[:100] + "..." if len(query) > 100 else query,
            "suggestions": [
                "Try a simpler query to test connection",
                "Check if the API service is available",
                "Verify environment configuration"
            ]
        }
        # Import here to avoid circular imports
        from utils.response_formatter import optimize_for_yaml
        import yaml
        return yaml.dump(optimize_for_yaml(error_response), default_flow_style=False)


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