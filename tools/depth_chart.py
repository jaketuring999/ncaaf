"""
Depth Chart MCP tools for college football data.
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
from utils.team_resolver import resolve_team_id
from queries.depth_chart import GET_DEPTH_CHART_QUERY


@mcp.tool()
async def GetDepthChart(
    team: Annotated[str, "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"],
    season: Annotated[Optional[Union[str, int]], "Season year (default: 2024)"] = 2024,
    offensive_only: Annotated[Optional[Union[str, bool]], "Show only offensive positions"] = False,
    defensive_only: Annotated[Optional[Union[str, bool]], "Show only defensive positions"] = False,
    include_special_teams: Annotated[Optional[Union[str, bool]], "Include special teams positions"] = True,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data"] = False
) -> str:
    """
    Get organized depth chart for a college football team.
    
    This tool provides a structured view of a team's roster organized by position groups
    (offense, defense, special teams) showing the likely starters and key backups.
    Much more useful than a raw roster dump.
    
    Args:
        team: Team name, abbreviation, or ID (e.g., "Alabama", "BAMA", "333")
        season: Season year (default: 2024)
        offensive_only: Show only offensive positions
        defensive_only: Show only defensive positions  
        include_special_teams: Include special teams positions (default: true)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        YAML formatted depth chart organized by position groups
        
    Examples:
        - GetDepthChart(team="Georgia") -> Full depth chart for Georgia
        - GetDepthChart(team="Alabama", offensive_only=true) -> Only offensive positions
        - GetDepthChart(team="Ohio State", defensive_only=true) -> Only defensive positions
    """
    # Convert and validate parameters
    team_id_int = await resolve_team_id(team)
    season_int = safe_int_conversion(season, 'season') if season is not None else 2024
    offensive_only_bool = safe_bool_conversion(offensive_only, 'offensive_only')
    defensive_only_bool = safe_bool_conversion(defensive_only, 'defensive_only')
    include_special_teams_bool = safe_bool_conversion(include_special_teams, 'include_special_teams')
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    # Build and execute query
    variables = build_query_variables(teamId=team_id_int, season=season_int)
    result = await execute_graphql(GET_DEPTH_CHART_QUERY, variables)
    
    # Format response as depth chart with filtering
    if include_raw_data_bool:
        return result
    else:
        context = {
            'offensive_only': offensive_only_bool,
            'defensive_only': defensive_only_bool, 
            'include_special_teams': include_special_teams_bool
        }
        return safe_format_response(result, 'depth_chart', include_raw_data_bool, context)