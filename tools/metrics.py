"""
Advanced metrics MCP tools for college football data.
"""

from typing import Optional, Union, Annotated
from fastmcp import Context

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql
from utils.param_utils import safe_int_conversion
from utils.graphql_utils import build_query_variables

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
    team_id: Annotated[Optional[Union[str, int]], "Team ID (can be string or int)"] = None,
    season: Annotated[Optional[Union[str, int]], "Season year (e.g., 2024 or '2024')"] = None,
    ctx: Context = None
) -> str:
    """
    Get advanced team metrics.
    
    Args:
        team_id: Team ID (can be string or int)
        season: Season year (e.g., 2024 or "2024")
    
    Returns:
        JSON string with advanced metrics data
    """
    # Convert string inputs to integers
    team_id_int = safe_int_conversion(team_id, 'team_id') if team_id is not None else None
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    
    variables = build_query_variables(teamId=team_id_int, season=season_int)
    return await execute_graphql(GET_ADVANCED_METRICS_QUERY, variables, ctx)