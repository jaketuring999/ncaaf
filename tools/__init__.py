"""
MCP Tools for College Football GraphQL Server

This package contains organized MCP tools for different college football data domains.
"""

# Import all tool modules to register their @mcp.tool decorators
# Specialized tools - the simple, working approach
from . import teams
from . import games
from . import rankings
from . import betting
from . import athletes
from . import metrics

# Power-user tools for advanced queries
from . import schema

__all__ = [
    # Specialized tools
    'teams',
    'games', 
    'rankings',
    'betting',
    'athletes',
    'metrics',
    # Power-user tools
    'schema'
]