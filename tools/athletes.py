"""
Athlete/Player-related MCP tools for college football data.
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

# GraphQL query for athlete data
GET_ATHLETES_QUERY = """
query GetAthletes($teamId: Int, $season: smallint) {
    athlete(
        where: {
            athleteTeams: {
                teamId: { _eq: $teamId }
                startYear: { _lte: $season }
                endYear: { _gte: $season }
            }
        }
        limit: 100
    ) {
        id
        name
        firstName
        lastName
        weight
        height
        jersey
        positionId
        teamId
        
        athleteTeams {
            teamId
            startYear
            endYear
            team {
                school
                abbreviation
                conference
            }
        }
    }
}
"""

GET_ATHLETES_QUERY_NO_SEASON = """
query GetAthletes($teamId: Int) {
    athlete(
        where: {
            athleteTeams: {
                teamId: { _eq: $teamId }
            }
        }
        limit: 100
    ) {
        id
        name
        firstName
        lastName
        weight
        height
        jersey
        positionId
        teamId
        
        athleteTeams {
            teamId
            startYear
            endYear
            team {
                school
                abbreviation
                conference
            }
        }
    }
}
"""

@mcp.tool()
async def GetAthletes(
    team: Annotated[Optional[str], "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"] = None,
    season: Annotated[Optional[Union[str, int]], "Season year (e.g., 2024 or '2024')"] = None,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False
) -> str:
    """
    Get athlete information for a team.
    
    Args:
        team: Team name, abbreviation, or ID (e.g., "Alabama", "BAMA", "333")
        season: Season year (e.g., 2024 or "2024")
    
    Returns:
        JSON string with athlete data
        include_raw_data: Include raw GraphQL response data (default: false)
    """
    # Convert string inputs to integers and resolve team
    team_id_int = await resolve_optional_team_id(team)
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    # Use different query based on whether season filtering is needed
    if season_int is not None:
        query = GET_ATHLETES_QUERY
        variables = build_query_variables(teamId=team_id_int, season=season_int)
    else:
        query = GET_ATHLETES_QUERY_NO_SEASON
        variables = build_query_variables(teamId=team_id_int)
    
    result = await execute_graphql(query, variables)
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'athletes', include_raw_data_bool)