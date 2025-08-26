"""
GraphQL queries for NCAAF MCP Server.

This module centralizes all GraphQL query definitions used by the MCP tools,
providing better organization and maintainability.
"""

from . import teams
from . import games
from . import betting
from . import rankings
from . import athletes
from . import metrics
from . import search

__all__ = [
    'teams',
    'games', 
    'betting',
    'rankings',
    'athletes',
    'metrics',
    'search'
]