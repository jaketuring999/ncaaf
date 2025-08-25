"""
MCP Tools for College Football GraphQL Server

This package contains organized MCP tools for different college football data domains.
"""

# Import all tool modules to register their @mcp.tool decorators
from . import teams
from . import games
from . import rankings
from . import betting
from . import athletes
from . import search
from . import metrics
from . import schema

__all__ = [
    'teams',
    'games', 
    'rankings',
    'betting',
    'athletes',
    'search',
    'metrics',
    'schema'
]