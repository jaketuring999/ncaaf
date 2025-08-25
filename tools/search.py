"""
Search and discovery MCP tools for college football data.
"""

from typing import Optional, Annotated

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql, build_query_variables

# Placeholder - will implement later
SEARCH_ENTITIES_QUERY = """
query SearchEntities($searchTerm: String!) {
    currentTeams(
        where: {
            school: { _ilike: $searchTerm }
        }
        limit: 10
    ) {
        teamId
        school
        conference
    }
}
"""

@mcp.tool()
async def SearchEntities(
    search_term: Annotated[str, "Text to search for across teams, players, and coaches"]
) -> str:
    """Search across teams, players, and coaches."""
    search_pattern = f"%{search_term}%"
    variables = build_query_variables(searchTerm=search_pattern)
    return await execute_graphql(SEARCH_ENTITIES_QUERY, variables)