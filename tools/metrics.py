"""
Advanced metrics MCP tools for college football data.
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
GET_ADVANCED_METRICS_QUERY = """
query GetAdvancedMetrics($teamId: Int, $season: smallint) {
    adjustedTeamMetrics(
        where: {
            teamId: { _eq: $teamId }
            year: { _eq: $season }
        }
    ) {
        teamId
        year
        epa
        epaAllowed
        explosiveness
        success
        team {
            school
        }
    }
}
"""

@mcp.tool()
async def GetAdvancedMetrics(
    team_id: Optional[int] = None,
    season: Optional[int] = None,
    ctx: Context = None
) -> str:
    """Get advanced team metrics."""
    variables = build_query_variables(teamId=team_id, season=season)
    return await execute_graphql(GET_ADVANCED_METRICS_QUERY, variables, ctx)