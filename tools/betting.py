"""
Betting-related MCP tools for college football data.
"""

from typing import Optional, Union, Annotated
from fastmcp import Context

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql
from utils.param_utils import safe_int_conversion, safe_bool_conversion, preprocess_betting_params
from utils.graphql_utils import build_query_variables
from utils.response_formatter import safe_format_response

# GraphQL queries for betting lines data
# Query with both season and week
GET_BETTING_LINES_WITH_SEASON_WEEK_QUERY = """
query GetBettingLines($season: smallint!, $week: smallint!, $limit: Int) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
            lines: {}
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

# Query with only season
GET_BETTING_LINES_WITH_SEASON_QUERY = """
query GetBettingLines($season: smallint!, $limit: Int) {
    game(
        where: {
            season: { _eq: $season }
            lines: {}
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

# Query with only week
GET_BETTING_LINES_WITH_WEEK_QUERY = """
query GetBettingLines($week: smallint!, $limit: Int) {
    game(
        where: {
            week: { _eq: $week }
            lines: {}
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

# Query with team ID
GET_BETTING_LINES_WITH_TEAM_QUERY = """
query GetBettingLines($teamId: Int!, $season: smallint, $limit: Int) {
    game(
        where: {
            _and: [
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
                { season: { _eq: $season } }
                { lines: {} }
            ]
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

# Query with team ID but no season
GET_BETTING_LINES_WITH_TEAM_NO_SEASON_QUERY = """
query GetBettingLines($teamId: Int!, $limit: Int) {
    game(
        where: {
            _and: [
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
                { lines: {} }
            ]
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

# Query with no filters (all games with betting lines)
GET_ALL_BETTING_LINES_QUERY = """
query GetBettingLines($limit: Int) {
    game(
        where: {
            lines: {}
        }
        orderBy: { startDate: DESC }
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

@mcp.tool() 
async def GetBettingLines(
    season: Annotated[Optional[Union[str, int]], "Season year (e.g., 2024 or '2024')"] = None,
    week: Annotated[Optional[Union[str, int]], "Week number (can be string or int)"] = None,
    team_id: Annotated[Optional[Union[str, int]], "Team ID (can be string or int)"] = None,
    limit: Annotated[Optional[Union[str, int]], "Maximum number of games to return (default: 50, can be string or int)"] = 50,
    calculate_records: Annotated[Union[str, bool], "Calculate ATS, Over/Under, and SU records (default: false)"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data (default: false)"] = False,
    ctx: Context = None
) -> str:
    """
    Get betting lines for games.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (can be string or int)
        team_id: Team ID (can be string or int)
        limit: Maximum number of games to return (default: 50, can be string or int)
        calculate_records: Calculate ATS, Over/Under, and SU records (default: false)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with betting lines data, optionally enhanced with betting analysis
    """
    # Process parameters using consolidated utility
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    params = preprocess_betting_params(
        season=season,
        week=week,
        team_id=team_id,
        limit=limit,
        calculate_records=calculate_records
    )
    
    # Extract processed values
    season_int = params.get('season')
    week_int = params.get('week')
    team_id_int = params.get('team_id')
    limit_int = params.get('limit')
    calculate_records_bool = params.get('calculate_records')
    
    # Select appropriate query based on which parameters are provided
    if team_id_int is not None:
        # Team-specific queries
        if season_int is not None:
            query = GET_BETTING_LINES_WITH_TEAM_QUERY
            variables = build_query_variables(teamId=team_id_int, season=season_int, limit=limit_int)
        else:
            query = GET_BETTING_LINES_WITH_TEAM_NO_SEASON_QUERY
            variables = build_query_variables(teamId=team_id_int, limit=limit_int)
    elif season_int is not None and week_int is not None:
        # Both season and week
        query = GET_BETTING_LINES_WITH_SEASON_WEEK_QUERY
        variables = build_query_variables(season=season_int, week=week_int, limit=limit_int)
    elif season_int is not None:
        # Only season
        query = GET_BETTING_LINES_WITH_SEASON_QUERY
        variables = build_query_variables(season=season_int, limit=limit_int)
    elif week_int is not None:
        # Only week
        query = GET_BETTING_LINES_WITH_WEEK_QUERY
        variables = build_query_variables(week=week_int, limit=limit_int)
    else:
        # No filters - get all games with betting lines
        query = GET_ALL_BETTING_LINES_QUERY
        variables = build_query_variables(limit=limit_int)
    
    # Execute the GraphQL query
    result = await execute_graphql(query, variables, ctx)
    
    # Add betting analysis if requested and we have a team_id
    if calculate_records_bool and team_id_int:
        try:
            # Import betting utilities
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.betting_utils import calculate_betting_analysis_from_graphql
            
            # Calculate betting analysis
            betting_analysis = calculate_betting_analysis_from_graphql(result, team_id_int)
            
            if betting_analysis and 'error' not in betting_analysis:
                # Parse the result to add betting summary (avoid duplication)
                import json
                result_data = json.loads(result)
                # Only add the summary, not the full game_details to avoid duplication
                result_data['betting_summary'] = betting_analysis.get('summary', betting_analysis)
                result = json.dumps(result_data, indent=2)
            elif betting_analysis and 'error' in betting_analysis:
                # Add error info but don't fail the whole query
                result_data = json.loads(result)
                result_data['betting_analysis_error'] = betting_analysis['error']
                result = json.dumps(result_data, indent=2)
                
        except Exception as e:
            # Don't fail the main query if betting analysis fails
            if ctx:
                await ctx.warning(f"Could not calculate betting analysis: {e}")
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'betting', include_raw_data_bool)