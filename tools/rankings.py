"""
Rankings-related MCP tools for college football data.
"""

from typing import Optional, Union, Annotated

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql  
from utils.param_utils import preprocess_ranking_params, safe_int_conversion, safe_bool_conversion
from utils.graphql_utils import build_query_variables
from utils.response_formatter import safe_format_response

# GraphQL query for rankings data
GET_RANKINGS_QUERY = """
query GetRankings($season: Int, $week: smallint) {
    poll(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: { week: ASC }
    ) {
        season
        seasonType
        week
        pollType {
            name
            abbreviation
        }
        rankings(
            orderBy: { rank: ASC }
        ) {
            rank
            firstPlaceVotes
            points
            team {
                teamId
                school
                conference
                abbreviation
            }
        }
    }
}
"""

@mcp.tool()
async def GetRankings(
    season: Annotated[Optional[Union[str, int]], "Season year"] = None,
    week: Annotated[Optional[Union[str, int]], "Week number"] = None,
    calculate_movement: Annotated[Union[str, bool], "Calculate ranking movement and trends"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data"] = False
) -> str:
    """
    Get college football rankings for a specific season and week.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (can be string or int)
        calculate_movement: Calculate ranking movement and trends (default: false)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with rankings data, optionally enhanced with movement analysis
    """
    # Convert string inputs to appropriate types
    season_int = safe_int_conversion(season, 'season') if season is not None else None
    week_int = safe_int_conversion(week, 'week') if week is not None else None
    calculate_movement_bool = safe_bool_conversion(calculate_movement, 'calculate_movement')
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    variables = build_query_variables(season=season_int, week=week_int)
    
    # Execute the GraphQL query
    result = await execute_graphql(GET_RANKINGS_QUERY, variables)
    
    # Add ranking movement analysis if requested
    if calculate_movement_bool:
        try:
            # Import ranking utilities
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.ranking_utils import calculate_ranking_movement_from_graphql
            
            # For movement analysis, we'd ideally need previous week's rankings
            # For now, we'll calculate poll consensus and basic analysis
            ranking_analysis = calculate_ranking_movement_from_graphql(result)
            
            if ranking_analysis and 'error' not in ranking_analysis:
                # Parse the result to add ranking analysis
                import json
                result_data = json.loads(result)
                result_data['ranking_analysis'] = ranking_analysis
                result = json.dumps(result_data, indent=2)
            elif ranking_analysis and 'error' in ranking_analysis:
                # Add error info but don't fail the whole query
                result_data = json.loads(result)
                result_data['ranking_analysis_error'] = ranking_analysis['error']
                result = json.dumps(result_data, indent=2)
                
        except Exception as e:
            # Don't fail the main query if ranking analysis fails
            pass  # Don't fail the main query if ranking analysis fails
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'rankings', include_raw_data_bool)