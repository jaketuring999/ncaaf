"""
Rankings-related MCP tools for college football data.
"""

import json
import sys
import os
from typing import Optional, Union, Annotated

# Import from server module at package level
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql  
from utils.param_utils import preprocess_ranking_params, safe_int_conversion, safe_bool_conversion
from utils.graphql_utils import build_query_variables
from utils.response_formatter import safe_format_response
from queries.rankings import build_rankings_query


async def get_latest_week(season: int) -> Optional[int]:
    """Get the latest week with ranking data for a given season."""
    try:
        query = """
        query GetLatestWeekForSeason($season: Int!) {
            poll(
                where: { season: { _eq: $season } }
                orderBy: { week: DESC }
                limit: 1
            ) {
                week
            }
        }
        """
        result = await execute_graphql(query, {"season": season})
        data = json.loads(result)
        
        if data.get("data", {}).get("poll") and len(data["data"]["poll"]) > 0:
            return data["data"]["poll"][0]["week"]
    except:
        pass
    
    return None


async def get_smart_defaults() -> tuple[int, int]:
    """Get smart default season and week for rankings."""
    current_season = 2025
    week = await get_latest_week(current_season)
    return current_season, week or 15


@mcp.tool()
async def GetRankings(
    season: Annotated[Optional[Union[str, int]], "Season year"] = None,
    week: Annotated[Optional[Union[str, int]], "Week number"] = None,
    poll_type: Annotated[Optional[str], "Filter by poll type (default: 'AP Top 25')"] = "AP Top 25",
    team: Annotated[Optional[str], "Search for specific team's ranking across polls"] = None,
    movement: Annotated[Union[str, bool], "Show ranking movement from previous week"] = False,
    top_n: Annotated[Optional[Union[str, int]], "Number of teams to show (default: 25)"] = 25,
    calculate_movement: Annotated[Union[str, bool], "Calculate ranking movement and trends (deprecated, use 'movement')"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data"] = False
) -> str:
    """
    Get college football rankings for a specific season and week.
    
    Args:
        season: Season year (e.g., 2025 or "2025")
        week: Week number (can be string or int)
        poll_type: Filter by poll type (default: "AP Top 25" for FBS focus)
        team: Search for specific team's ranking across all major polls
        movement: Show ranking movement from previous week (default: false)
        top_n: Number of teams to show (default: 25 for full rankings)
        calculate_movement: Calculate ranking movement and trends (deprecated, use 'movement')
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        YAML formatted rankings data, optimized for single poll or team search
    """
    # Convert string inputs to appropriate types
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    week_int = safe_int_conversion(week, 'week') if week is not None else None
    top_n_int = safe_int_conversion(top_n, 'top_n') if top_n is not None else 25
    movement_bool = safe_bool_conversion(movement, 'movement') or safe_bool_conversion(calculate_movement, 'calculate_movement')
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    # Apply smart defaults
    if season_int is None and week_int is None:
        season_int, week_int = await get_smart_defaults()
    elif season_int is None:
        season_int = 2025
    elif week_int is None:
        week_int = await get_latest_week(season_int) or 15
    
    # Build dynamic query and variables
    query, variables = build_rankings_query(
        season=season_int, 
        week=week_int, 
        poll_type=poll_type,
        team=team,
        top_n=top_n_int
    )
    
    # Execute the GraphQL query
    result = await execute_graphql(query, variables)
    
    # Add ranking movement analysis if requested
    if movement_bool and week_int and week_int > 1:
        try:
            # Get previous week's rankings for comparison
            prev_query, prev_variables = build_rankings_query(
                season=season_int, 
                week=week_int-1, 
                poll_type=poll_type,
                team=team,
                top_n=top_n_int
            )
            prev_result = await execute_graphql(prev_query, prev_variables)
            
            # Add movement data to current result
            result_data = json.loads(result)
            prev_data = json.loads(prev_result)
            result_data['previous_week_data'] = prev_data.get('data', {})
            result = json.dumps(result_data, indent=2)
                
        except Exception:
            # Don't fail the main query if movement analysis fails
            pass
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'rankings', include_raw_data_bool, {
            'poll_type': poll_type,
            'team': team,
            'movement': movement_bool,
            'top_n': top_n_int
        })