"""
Athlete/Player-related MCP tools for college football data.
"""

from typing import Optional
from fastmcp import Context

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.mcp_server import mcp
from src.graphql_executor import execute_graphql, build_query_variables

# Placeholder - will implement later
GET_ATHLETES_QUERY = """
query GetAthletes($teamId: Int, $season: smallint) {
    athletes(
        where: {
            teamId: { _eq: $teamId }
            season: { _eq: $season }
        }
    ) {
        id
        name
        position
        jersey
        year
        weight
        height
        hometown
        team {
            school
        }
    }
}
"""

@mcp.tool()
async def GetAthletes(
    team_id: Optional[int] = None,
    season: Optional[int] = None,
    ctx: Context = None
) -> str:
    """Get athlete information for a team."""
    variables = build_query_variables(teamId=team_id, season=season)
    return await execute_graphql(GET_ATHLETES_QUERY, variables, ctx)