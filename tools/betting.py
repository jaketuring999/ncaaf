"""
Betting-related MCP tools for college football data.
"""

from typing import Optional, Union, Annotated

# Import from server module at package level
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcp_instance import mcp
from src.graphql_executor import execute_graphql
from utils.param_utils import safe_int_conversion, safe_bool_conversion, preprocess_betting_params
from utils.graphql_utils import build_query_variables
from utils.response_formatter import safe_format_response
from utils.team_resolver import resolve_optional_team_id

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
    season: Annotated[Optional[Union[str, int]], "Season year"] = None,
    week: Annotated[Optional[Union[str, int]], "Week number"] = None,
    team: Annotated[Optional[str], "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"] = None,
    limit: Annotated[Optional[Union[str, int]], "Maximum number of games to return"] = 50,
    calculate_records: Annotated[Union[str, bool], "Calculate ATS, Over/Under, and SU records"] = False,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data"] = False
) -> str:
    """
    Get betting lines for games.
    
    Args:
        season: Season year (e.g., 2024 or "2024")
        week: Week number (can be string or int)
        team: Team name, abbreviation, or ID (e.g., "Alabama", "BAMA", "333")
        limit: Maximum number of games to return (default: 50, can be string or int)
        calculate_records: Calculate ATS, Over/Under, and SU records (default: false)
        include_raw_data: Include raw GraphQL response data (default: false)
    
    Returns:
        JSON string with betting lines data, optionally enhanced with betting analysis
    """
    # Process parameters using consolidated utility
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    # Resolve team to ID if provided
    team_id = await resolve_optional_team_id(team)
    
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
    result = await execute_graphql(query, variables)
    
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
            pass  # Don't fail the main query if betting analysis fails
    
    # Format response based on include_raw_data flag
    if include_raw_data_bool:
        return result
    else:
        return safe_format_response(result, 'betting', include_raw_data_bool)


@mcp.tool()
async def GetBettingAnalysis(
    team: Annotated[str, "Team name, abbreviation, or ID (e.g., 'Alabama', 'BAMA', '333')"],
    opponent: Annotated[Optional[str], "Opponent team name, abbreviation, or ID for head-to-head analysis"] = None,
    analysis_type: Annotated[str, "Analysis type: 'spread_ranges', 'over_under', 'h2h', 'trends', or 'all' (default)"] = "all",
    season: Annotated[Optional[Union[str, int]], "Season year"] = None,
    scenario: Annotated[Optional[str], "Betting scenario: 'road_underdog', 'home_favorite', 'road_favorite', 'home_underdog'"] = None,
    last_n_games: Annotated[Optional[Union[str, int]], "Number of recent games for trend analysis"] = 10,
    include_raw_data: Annotated[Union[str, bool], "Include raw GraphQL response data"] = False
) -> str:
    """
    Advanced betting analysis tool for specific analytical questions.
    
    Provides targeted betting insights based on analysis_type:
    - spread_ranges: How team performs at different spread levels (underdog vs favorite)
    - over_under: Over/Under performance at different total ranges
    - h2h: Head-to-head betting record with specific opponent 
    - trends: Recent betting trends and home/away splits
    - all: Complete analysis package with multiple insights

    Scenario filtering allows targeting specific betting situations:
    - road_underdog: Away games where team is underdog (spread > 0)
    - home_favorite: Home games where team is favorite (spread < 0)  
    - road_favorite: Away games where team is favorite (spread < 0)
    - home_underdog: Home games where team is underdog (spread > 0)
    
    Example queries:
    - "How does Alabama perform as a road underdog?" → scenario="road_underdog"
    - "Georgia's record as home favorite?" → scenario="home_favorite"
    
    Args:
        team: Team name, abbreviation, or ID to analyze
        opponent: Opponent team name, abbreviation, or ID for head-to-head analysis
        analysis_type: Type of analysis to perform
        season: Season year (default: current season)
        scenario: Filter by betting scenario (home/away + spread position)
        last_n_games: Number of recent games for trend analysis
        include_raw_data: Include raw GraphQL response data
        
    Returns:
        YAML formatted betting analysis with actionable insights
    """
    # Process parameters
    from utils.param_utils import safe_int_conversion, safe_bool_conversion, preprocess_betting_params
    from utils.graphql_utils import build_query_variables
    from utils.response_formatter import create_formatted_response
    from utils.betting_utils import (
        analyze_spread_ranges, 
        analyze_head_to_head, 
        analyze_betting_trends,
        analyze_over_under_ranges,
        format_betting_analysis_response
    )
    
    # Resolve team names to IDs
    from utils.team_resolver import resolve_team_id, resolve_optional_team_id
    
    team_id_int = await resolve_team_id(team)
    opponent_id_int = await resolve_optional_team_id(opponent)
    season_int = safe_int_conversion(season, 'season') if season else None
    last_n_games_int = safe_int_conversion(last_n_games, 'last_n_games') if last_n_games else 10
    include_raw_data_bool = safe_bool_conversion(include_raw_data, 'include_raw_data')
    
    if not team_id_int:
        return create_formatted_response(
            '{"error": "Invalid team_id"}',
            {"error": "Invalid team_id provided"},
            [],
            include_raw_data_bool
        )
    
    # Determine which GraphQL query to use (reuse existing queries from GetBettingLines)
    if season_int:
        query = GET_BETTING_LINES_WITH_TEAM_QUERY
        variables = build_query_variables(teamId=team_id_int, season=season_int, limit=100)
    else:
        query = GET_BETTING_LINES_WITH_TEAM_NO_SEASON_QUERY
        variables = build_query_variables(teamId=team_id_int, limit=100)
    
    # Execute the GraphQL query to get raw game data
    try:
        result = await execute_graphql(query, variables)
        
        # Parse games from GraphQL result
        import json
        data = json.loads(result)
        games = data.get('data', {}).get('game', [])
        
        if not games:
            return create_formatted_response(
                result,
                {"error": "No games found for this team", "team_id": team_id_int},
                [],
                include_raw_data_bool
            )
        
        # Get team name from first game
        team_name = None
        for game in games:
            home_team_info = game.get('homeTeamInfo', {})
            away_team_info = game.get('awayTeamInfo', {})
            
            if home_team_info.get('teamId') == team_id_int:
                team_name = home_team_info.get('school')
                break
            elif away_team_info.get('teamId') == team_id_int:
                team_name = away_team_info.get('school')
                break
        
        if not team_name:
            return create_formatted_response(
                result,
                {"error": "Could not determine team name", "team_id": team_id_int},
                [],
                include_raw_data_bool
            )
        
        # Get opponent name if doing H2H analysis
        opponent_name = None
        if opponent_id_int and analysis_type in ['h2h', 'all']:
            # Get opponent name from GraphQL directly to avoid circular imports
            from utils.graphql_utils import build_query_variables
            
            GET_TEAM_NAME_QUERY = """
            query GetTeamName($teamId: Int!) {
                currentTeams(where: { teamId: { _eq: $teamId } }) {
                    school
                }
            }
            """
            
            try:
                team_variables = build_query_variables(teamId=opponent_id_int)
                team_result = await execute_graphql(GET_TEAM_NAME_QUERY, team_variables)
                team_data = json.loads(team_result)
                teams = team_data.get('data', {}).get('currentTeams', [])
                if teams:
                    opponent_name = teams[0].get('school')
            except:
                pass  # If we can't get opponent name, skip H2H analysis
        
        # Apply scenario filter if provided
        from utils.betting_utils import filter_games_by_scenario
        filtered_games = filter_games_by_scenario(games, team_name, scenario) if scenario else games
        
        # Perform requested analysis
        analysis_results = {}
        
        if analysis_type in ['spread_ranges', 'all']:
            spread_analysis = analyze_spread_ranges(filtered_games, team_name)
            analysis_results['spread_ranges'] = spread_analysis
        
        if analysis_type in ['h2h', 'all'] and opponent_name:
            h2h_analysis = analyze_head_to_head(filtered_games, team_name, opponent_name)
            analysis_results['h2h'] = h2h_analysis
        
        if analysis_type in ['over_under', 'all']:
            ou_analysis = analyze_over_under_ranges(filtered_games, team_name)
            analysis_results['over_under'] = ou_analysis
        
        if analysis_type in ['trends', 'all']:
            trend_analysis = analyze_betting_trends(filtered_games, team_name, last_n_games_int)
            analysis_results['trends'] = trend_analysis
        
        # Format response based on analysis type
        if analysis_type == 'all':
            # Combined analysis - create comprehensive summary
            summary = {
                "team": team_name,
                "analysis_type": "Complete Betting Analysis",
                "total_games_analyzed": len(filtered_games),
                "season": season_int if season_int else "All seasons",
                "scenario": scenario if scenario else "All games"
            }
            
            formatted_entries = []
            
            # Add spread range results
            if 'spread_ranges' in analysis_results:
                spread_data = analysis_results['spread_ranges']
                for range_key, range_info in spread_data.items():
                    if isinstance(range_info, dict) and range_info.get('games', 0) > 0:
                        entry = {
                            "analysis": "Spread Range",
                            "range": range_info['display_name'],
                            "games": range_info['games'],
                            "ats_record": range_info['ats_record'],
                            "ats_percentage": f"{range_info['ats_percentage']}%"
                        }
                        formatted_entries.append(entry)
            
            # Add O/U results if available
            if 'over_under' in analysis_results:
                ou_data = analysis_results['over_under']
                for range_key, range_info in ou_data.items():
                    if isinstance(range_info, dict) and range_info.get('games', 0) > 0:
                        entry = {
                            "analysis": "O/U Range",
                            "total_range": range_info['display_name'],
                            "games": range_info['games'],
                            "over_record": range_info['over_record'],
                            "over_percentage": f"{range_info['over_percentage']}%"
                        }
                        formatted_entries.append(entry)
            
            # Add H2H results if available
            if 'h2h' in analysis_results:
                h2h_data = analysis_results['h2h']
                if h2h_data.get('total_games', 0) > 0:
                    all_time = h2h_data.get('all_time_record', {})
                    entry = {
                        "analysis": "Head-to-Head vs " + opponent_name,
                        "total_games": h2h_data['total_games'],
                        "ats_record": all_time.get('ats_record', 'N/A'),
                        "ats_percentage": f"{all_time.get('ats_percentage', 0)}%"
                    }
                    formatted_entries.append(entry)
            
            # Add trend results
            if 'trends' in analysis_results:
                trend_data = analysis_results['trends']
                overall = trend_data.get('overall_trends', {})
                entry = {
                    "analysis": trend_data.get('analysis_period', 'Recent Trends'),
                    "ats_record": overall.get('ats_record', 'N/A'),
                    "ats_percentage": f"{overall.get('ats_percentage', 0)}%",
                    "note": "Recent performance trends"
                }
                formatted_entries.append(entry)
            
            return create_formatted_response(result, summary, formatted_entries, include_raw_data_bool)
        
        else:
            # Single analysis type
            if analysis_type in analysis_results:
                analysis_data = analysis_results[analysis_type]
                formatted_response = format_betting_analysis_response(analysis_data, team_name, analysis_type)
                
                return create_formatted_response(
                    result, 
                    formatted_response['summary'], 
                    formatted_response['entries'], 
                    include_raw_data_bool
                )
            else:
                return create_formatted_response(
                    result,
                    {"error": f"Analysis type '{analysis_type}' not available or no data"},
                    [],
                    include_raw_data_bool
                )
        
    except Exception as e:
        error_summary = {
            "error": f"Failed to perform betting analysis: {str(e)}",
            "team_id": team_id_int,
            "analysis_type": analysis_type
        }
        return create_formatted_response('{"error": "GraphQL query failed"}', error_summary, [], include_raw_data_bool)