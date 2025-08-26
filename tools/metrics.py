"""
Advanced metrics MCP tools for college football data.
"""

from typing import Optional, Union, Annotated

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql
from utils.param_utils import safe_int_conversion, safe_bool_conversion
from utils.graphql_utils import build_query_variables
from utils.response_formatter import safe_format_response
from utils.team_resolver import resolve_optional_team_id

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
    team: Annotated[Optional[str], "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"] = None,
    season: Annotated[Optional[Union[str, int]], "Season year (e.g., 2024 or '2024')"] = None,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False
) -> str:
    """
    Get advanced team metrics.
    
    Args:
        team: Team name, abbreviation, or ID (e.g., "Alabama", "BAMA", "333")
        season: Season year (e.g., 2024 or "2024")
    
    Returns:
        JSON string with advanced metrics data
        include_raw_data: Include raw GraphQL response data (default: false)
    """
    # Convert string inputs to integers and resolve team
    team_id_int = await resolve_optional_team_id(team)
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    variables = build_query_variables(teamId=team_id_int, season=season_int)
    result = await execute_graphql(GET_ADVANCED_METRICS_QUERY, variables)
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'metrics', include_raw_data_bool)