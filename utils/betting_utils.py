"""
Betting calculation utilities for college football betting analysis.

Simple, pure functions to calculate ATS, O/U, and other betting outcomes
from GraphQL query results.
"""

from typing import List, Dict, Any, Optional, Tuple
import json


def calculate_ats_outcome(
    home_points: int, 
    away_points: int, 
    spread: float,
    team_name: str,
    home_team: str,
    away_team: str
) -> bool:
    """
    Calculate if a team covered the spread (ATS = Against The Spread).
    
    Args:
        home_points: Home team final score
        away_points: Away team final score  
        spread: Betting spread (negative = home team favored, positive = away team favored)
        team_name: Name of team we're analyzing
        home_team: Home team name
        away_team: Away team name
        
    Returns:
        True if the team covered the spread, False otherwise
    """
    margin = home_points - away_points  # Positive = home team won by this margin
    
    # Better team name matching - check if team name is contained in either team name
    team_lower = team_name.lower()
    is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
    
    if is_home_team:
        # Team is home - they cover if they beat the spread
        # If spread is -10.5, home team needs to win by MORE than 10.5
        # If spread is +3.5, home team just needs to lose by LESS than 3.5 (or win)
        return margin > abs(spread) if spread < 0 else margin > -spread
    else:
        # Team is away - they cover if they beat the spread  
        # If spread is -10.5 (home favored), away team covers by losing by LESS than 10.5 (or winning)
        # If spread is +3.5 (away favored), away team needs to win by MORE than 3.5
        return -margin < abs(spread) if spread < 0 else -margin > spread


def calculate_ou_outcome(
    home_points: int,
    away_points: int, 
    over_under: float
) -> bool:
    """
    Calculate if the total went over the betting total.
    
    Args:
        home_points: Home team final score
        away_points: Away team final score
        over_under: Betting total/over-under line
        
    Returns:
        True if total went over, False if under
    """
    try:
        total = safe_numeric_conversion(home_points) + safe_numeric_conversion(away_points)
        ou_line = safe_numeric_conversion(over_under)
        if ou_line is None:
            return False
        return total > ou_line
    except:
        return False


def safe_numeric_conversion(value):
    """
    Convert GraphQL numeric/string to float safely.
    
    Args:
        value: Value to convert (can be string, int, float, or None)
        
    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_su_outcome(
    team_points: int,
    opponent_points: int
) -> bool:
    """
    Calculate straight-up (SU) win.
    
    Args:
        team_points: Team's final score
        opponent_points: Opponent's final score
        
    Returns:
        True if team won straight-up, False otherwise
    """
    return team_points > opponent_points


def calculate_team_betting_record(
    games: List[Dict[str, Any]], 
    team_name: str
) -> Dict[str, Any]:
    """
    Calculate complete betting record for a team from game data.
    
    Args:
        games: List of game dictionaries from GraphQL query
        team_name: Name of team to analyze
        
    Returns:
        Dictionary with ATS, O/U, and SU records
    """
    ats_wins = 0
    ou_overs = 0
    su_wins = 0
    total_games = 0
    
    for game in games:
        # Skip games without complete data
        if not all([
            game.get('homePoints') is not None,
            game.get('awayPoints') is not None,
            game.get('lines') and len(game['lines']) > 0,
            game['lines'][0].get('spread') is not None
        ]):
            continue
            
        home_points = safe_numeric_conversion(game['homePoints'])
        away_points = safe_numeric_conversion(game['awayPoints'])
        home_team = game.get('homeTeam', '')
        away_team = game.get('awayTeam', '')
        
        # Get betting lines (use first line if multiple)
        line = game['lines'][0]
        spread = safe_numeric_conversion(line['spread'])
        over_under = safe_numeric_conversion(line.get('overUnder'))
        
        total_games += 1
        
        # Calculate ATS outcome
        if calculate_ats_outcome(home_points, away_points, spread, team_name, home_team, away_team):
            ats_wins += 1
            
        # Calculate O/U outcome  
        if over_under and calculate_ou_outcome(home_points, away_points, over_under):
            ou_overs += 1
            
        # Calculate SU outcome - use same matching logic as ATS
        team_lower = team_name.lower()
        is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
        
        if is_home_team:
            team_points, opponent_points = home_points, away_points
        else:
            team_points, opponent_points = away_points, home_points
            
        if calculate_su_outcome(team_points, opponent_points):
            su_wins += 1
    
    # Format records as strings
    ats_record = f"{ats_wins}-{total_games - ats_wins}" if total_games > 0 else "0-0"
    ou_record = f"{ou_overs}-{total_games - ou_overs}" if total_games > 0 else "0-0"
    su_record = f"{su_wins}-{total_games - su_wins}" if total_games > 0 else "0-0"
    
    return {
        "ats": ats_record,
        "ou": ou_record, 
        "su": su_record,
        "total_games": total_games,
        "ats_percentage": round(ats_wins / total_games * 100, 1) if total_games > 0 else 0.0,
        "ou_percentage": round(ou_overs / total_games * 100, 1) if total_games > 0 else 0.0,
        "su_percentage": round(su_wins / total_games * 100, 1) if total_games > 0 else 0.0
    }


def calculate_weekly_betting_trends(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate betting trends for a week of games.
    
    Args:
        games: List of game dictionaries from GraphQL query
        
    Returns:
        Dictionary with weekly betting statistics
    """
    favorites_covered = 0
    overs_hit = 0
    total_games = 0
    
    for game in games:
        # Skip games without complete data
        if not all([
            game.get('homePoints') is not None,
            game.get('awayPoints') is not None,
            game.get('lines') and len(game['lines']) > 0
        ]):
            continue
            
        home_points = safe_numeric_conversion(game['homePoints'])
        away_points = safe_numeric_conversion(game['awayPoints'])
        line = game['lines'][0]
        spread = safe_numeric_conversion(line.get('spread'))
        over_under = safe_numeric_conversion(line.get('overUnder'))
        
        if spread is None:
            continue
            
        total_games += 1
        
        # Check if favorite covered (spread > 0 means home favored)
        margin = home_points - away_points
        if spread > 0:  # Home team favored
            favorite_covered = margin > spread
        else:  # Away team favored  
            favorite_covered = margin < spread
            
        if favorite_covered:
            favorites_covered += 1
            
        # Check over/under
        if over_under and calculate_ou_outcome(home_points, away_points, over_under):
            overs_hit += 1
    
    return {
        "total_games": total_games,
        "favorites_covered": favorites_covered,
        "favorites_percentage": round(favorites_covered / total_games * 100, 1) if total_games > 0 else 0.0,
        "overs_hit": overs_hit, 
        "overs_percentage": round(overs_hit / total_games * 100, 1) if total_games > 0 else 0.0,
        "unders_hit": total_games - overs_hit,
        "unders_percentage": round((total_games - overs_hit) / total_games * 100, 1) if total_games > 0 else 0.0
    }


def analyze_spread_ranges(games: List[Dict[str, Any]], team_name: str) -> Dict[str, Any]:
    """
    Analyze team performance at different spread levels.
    
    Args:
        games: List of game dictionaries from GraphQL query
        team_name: Name of team to analyze
        
    Returns:
        Dictionary with performance breakdown by spread range
    """
    # Define spread ranges with clear labels
    range_definitions = [
        ("heavy_underdog", 14.5, float('inf'), "14.5+ underdog"),
        ("underdog", 3.5, 14.4, "3.5-14.4 underdog"),
        ("slight_underdog", 0.1, 3.4, "0.1-3.4 underdog"),
        ("pick_em", -0.1, 0.1, "Pick'em"),
        ("slight_favorite", -3.4, -0.1, "0.1-3.4 favorite"),
        ("favorite", -14.4, -3.5, "3.5-14.4 favorite"),
        ("heavy_favorite", -float('inf'), -14.5, "14.5+ favorite")
    ]
    
    range_performance = {}
    
    for range_key, min_spread, max_spread, display_name in range_definitions:
        range_games = []
        
        for game in games:
            if not all([
                game.get('homePoints') is not None,
                game.get('awayPoints') is not None,
                game.get('lines') and len(game['lines']) > 0,
                game['lines'][0].get('spread') is not None
            ]):
                continue
                
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            line = game['lines'][0]
            spread = safe_numeric_conversion(line['spread'])
            
            # Skip if spread conversion failed
            if spread is None:
                continue
            
            # Determine if team is home or away and calculate their effective spread
            team_lower = team_name.lower()
            is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
            
            if is_home_team:
                team_spread = spread  # Positive = underdog, negative = favorite
            else:
                team_spread = -spread  # Flip spread for away team perspective
            
            # Check if this game falls in the current range
            if min_spread <= team_spread <= max_spread:
                range_games.append(game)
        
        if range_games:
            # Calculate betting record for this range
            range_record = calculate_team_betting_record(range_games, team_name)
            range_performance[range_key] = {
                "display_name": display_name,
                "games": len(range_games),
                "ats_record": range_record["ats"],
                "ats_percentage": range_record["ats_percentage"],
                "su_record": range_record["su"],
                "su_percentage": range_record["su_percentage"]
            }
    
    return range_performance


def analyze_head_to_head(
    games: List[Dict[str, Any]], 
    team1_name: str, 
    team2_name: str
) -> Dict[str, Any]:
    """
    Analyze head-to-head betting records between two teams.
    
    Args:
        games: List of game dictionaries from GraphQL query
        team1_name: First team name
        team2_name: Second team name (opponent)
        
    Returns:
        Dictionary with head-to-head betting analysis
    """
    h2h_games = []
    
    # Filter to only games where both teams played each other
    for game in games:
        home_team = game.get('homeTeam', '').lower()
        away_team = game.get('awayTeam', '').lower()
        team1_lower = team1_name.lower()
        team2_lower = team2_name.lower()
        
        # Check if this is a matchup between the two teams
        is_matchup = (
            (team1_lower in home_team or home_team in team1_lower) and
            (team2_lower in away_team or away_team in team2_lower)
        ) or (
            (team1_lower in away_team or away_team in team1_lower) and
            (team2_lower in home_team or home_team in team2_lower)
        )
        
        if is_matchup:
            h2h_games.append(game)
    
    if not h2h_games:
        return {
            "total_games": 0,
            "team1_record": team1_name,
            "team2_record": team2_name,
            "note": "No head-to-head games found"
        }
    
    # Calculate betting records for team1
    team1_record = calculate_team_betting_record(h2h_games, team1_name)
    
    # Calculate recent trends (last 5 games if available)
    recent_games = h2h_games[-5:] if len(h2h_games) >= 5 else h2h_games
    recent_record = calculate_team_betting_record(recent_games, team1_name) if recent_games else None
    
    return {
        "total_games": len(h2h_games),
        "matchup": f"{team1_name} vs {team2_name}",
        "all_time_record": {
            "ats_record": team1_record["ats"],
            "ats_percentage": team1_record["ats_percentage"],
            "su_record": team1_record["su"], 
            "su_percentage": team1_record["su_percentage"]
        },
        "recent_record": {
            "games": len(recent_games),
            "ats_record": recent_record["ats"] if recent_record else "N/A",
            "ats_percentage": recent_record["ats_percentage"] if recent_record else 0,
            "su_record": recent_record["su"] if recent_record else "N/A"
        } if recent_record else None
    }


def filter_games_by_scenario(games: List[Dict[str, Any]], team_name: str, scenario: str) -> List[Dict[str, Any]]:
    """
    Filter games based on betting scenario (home/away + spread position).
    
    Args:
        games: List of game dictionaries from GraphQL query
        team_name: Name of team to analyze
        scenario: Scenario type - 'road_underdog', 'home_favorite', 'road_favorite', 'home_underdog'
        
    Returns:
        Filtered list of games matching the scenario
    """
    if not scenario:
        return games
    
    valid_scenarios = ['road_underdog', 'home_favorite', 'road_favorite', 'home_underdog']
    if scenario not in valid_scenarios:
        return games
    
    filtered_games = []
    
    for game in games:
        # Skip games without complete data
        if not all([
            game.get('homePoints') is not None,
            game.get('awayPoints') is not None,
            game.get('lines') and len(game['lines']) > 0,
            game['lines'][0].get('spread') is not None
        ]):
            continue
            
        # Determine if team is home or away
        home_team = game.get('homeTeam', '')
        team_lower = team_name.lower()
        is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
        
        # Get spread for this team
        line = game['lines'][0]
        spread = safe_numeric_conversion(line['spread'])
        if spread is None:
            continue
            
        # Calculate team's effective spread (positive = underdog, negative = favorite)
        if is_home_team:
            team_spread = spread
        else:
            team_spread = -spread
        
        # Check if game matches the scenario
        scenario_match = False
        
        if scenario == "road_underdog" and not is_home_team and team_spread > 0:
            scenario_match = True
        elif scenario == "home_favorite" and is_home_team and team_spread < 0:
            scenario_match = True
        elif scenario == "road_favorite" and not is_home_team and team_spread < 0:
            scenario_match = True
        elif scenario == "home_underdog" and is_home_team and team_spread > 0:
            scenario_match = True
        
        if scenario_match:
            filtered_games.append(game)
    
    return filtered_games


def analyze_betting_trends(games: List[Dict[str, Any]], team_name: str, last_n_games: int = 10) -> Dict[str, Any]:
    """
    Analyze recent betting trends for a team.
    
    Args:
        games: List of game dictionaries from GraphQL query (should be ordered by date DESC)
        team_name: Name of team to analyze
        last_n_games: Number of recent games to analyze
        
    Returns:
        Dictionary with recent betting trends including scenario breakdowns
    """
    if not games:
        return {"error": "No games provided for trend analysis"}
    
    # Take the most recent N games
    recent_games = games[:last_n_games]
    
    # Calculate overall record for recent games
    recent_record = calculate_team_betting_record(recent_games, team_name)
    
    # Calculate home vs away splits
    home_games = []
    away_games = []
    
    for game in recent_games:
        if not all([
            game.get('homePoints') is not None,
            game.get('awayPoints') is not None,
            game.get('lines') and len(game['lines']) > 0
        ]):
            continue
            
        home_team = game.get('homeTeam', '')
        team_lower = team_name.lower()
        is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
        
        if is_home_team:
            home_games.append(game)
        else:
            away_games.append(game)
    
    home_record = calculate_team_betting_record(home_games, team_name) if home_games else None
    away_record = calculate_team_betting_record(away_games, team_name) if away_games else None
    
    # Calculate scenario breakdowns
    scenario_performance = {}
    scenarios = ['road_underdog', 'home_favorite', 'road_favorite', 'home_underdog']
    
    for scenario in scenarios:
        scenario_games = filter_games_by_scenario(recent_games, team_name, scenario)
        if scenario_games:
            scenario_record = calculate_team_betting_record(scenario_games, team_name)
            
            # Calculate average spread for this scenario
            spreads = []
            for game in scenario_games:
                if game.get('lines') and len(game['lines']) > 0:
                    home_team = game.get('homeTeam', '')
                    is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
                    spread = safe_numeric_conversion(game['lines'][0].get('spread'))
                    if spread is not None:
                        team_spread = spread if is_home_team else -spread
                        spreads.append(team_spread)
            
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
            
            scenario_performance[scenario] = {
                "games": len(scenario_games),
                "ats_record": scenario_record["ats"],
                "ats_percentage": scenario_record["ats_percentage"],
                "su_record": scenario_record["su"],
                "su_percentage": scenario_record["su_percentage"],
                "avg_spread": round(avg_spread, 1)
            }
    
    return {
        "analysis_period": f"Last {len(recent_games)} games",
        "overall_trends": {
            "ats_record": recent_record["ats"],
            "ats_percentage": recent_record["ats_percentage"],
            "su_record": recent_record["su"],
            "su_percentage": recent_record["su_percentage"]
        },
        "home_vs_away": {
            "home_games": len(home_games),
            "home_ats_record": home_record["ats"] if home_record else "N/A",
            "home_ats_percentage": home_record["ats_percentage"] if home_record else 0,
            "away_games": len(away_games),
            "away_ats_record": away_record["ats"] if away_record else "N/A", 
            "away_ats_percentage": away_record["ats_percentage"] if away_record else 0
        },
        "scenario_performance": scenario_performance
    }


def analyze_over_under_ranges(games: List[Dict[str, Any]], team_name: str) -> Dict[str, Any]:
    """
    Analyze team O/U performance at different total ranges.
    
    Args:
        games: List of game dictionaries from GraphQL query
        team_name: Name of team to analyze
        
    Returns:
        Dictionary with O/U performance breakdown by total range
    """
    # Define total ranges with clear labels
    ranges = [
        ("low_totals", 0, 45, "Under 45 points"),
        ("medium_low", 45, 55, "45-55 points"),
        ("medium", 55, 65, "55-65 points"),
        ("medium_high", 65, 75, "65-75 points"),
        ("high_totals", 75, 999, "Over 75 points")
    ]
    
    range_performance = {}
    
    for range_key, min_total, max_total, display_name in ranges:
        range_games = []
        overs = 0
        unders = 0
        
        for game in games:
            # Skip games without complete data
            if not all([
                game.get('homePoints') is not None,
                game.get('awayPoints') is not None,
                game.get('lines') and len(game['lines']) > 0,
                game['lines'][0].get('overUnder') is not None
            ]):
                continue
                
            line = game['lines'][0]
            over_under = safe_numeric_conversion(line.get('overUnder'))
            if not over_under:
                continue
                
            # Check if O/U line falls in this range
            if min_total <= over_under < max_total:
                home_points = safe_numeric_conversion(game.get('homePoints'))
                away_points = safe_numeric_conversion(game.get('awayPoints'))
                
                if home_points is not None and away_points is not None:
                    actual_total = home_points + away_points
                    range_games.append(game)
                    
                    if actual_total > over_under:
                        overs += 1
                    else:
                        unders += 1
        
        if range_games:
            over_pct = round(overs/len(range_games)*100, 1) if range_games else 0
            range_performance[range_key] = {
                "display_name": display_name,
                "games": len(range_games),
                "over_record": f"{overs}-{unders}",
                "over_percentage": over_pct,
                "under_percentage": round(100 - over_pct, 1)
            }
    
    return range_performance


def format_betting_analysis_response(
    analysis_data: Dict[str, Any], 
    team_name: str, 
    analysis_type: str
) -> Dict[str, Any]:
    """
    Format betting analysis data for YAML output using response_formatter pattern.
    
    Args:
        analysis_data: Analysis results from utility functions
        team_name: Team being analyzed
        analysis_type: Type of analysis performed
        
    Returns:
        Dictionary formatted for create_formatted_response()
    """
    if analysis_type == "spread_ranges":
        summary = {
            "team": team_name,
            "analysis_type": "Spread Range Performance",
            "total_ranges_analyzed": len([k for k, v in analysis_data.items() if isinstance(v, dict) and v.get('games', 0) > 0])
        }
        
        formatted_entries = []
        for range_key, range_data in analysis_data.items():
            if isinstance(range_data, dict) and range_data.get('games', 0) > 0:
                entry = {
                    "spread_range": range_data["display_name"],
                    "games_played": range_data["games"],
                    "ats_record": range_data["ats_record"],
                    "ats_percentage": f"{range_data['ats_percentage']}%",
                    "su_record": range_data["su_record"],
                    "su_percentage": f"{range_data['su_percentage']}%"
                }
                formatted_entries.append(entry)
        
        return {"summary": summary, "entries": formatted_entries}
    
    elif analysis_type == "h2h":
        summary = {
            "matchup": analysis_data.get("matchup", "Unknown matchup"),
            "analysis_type": "Head-to-Head Betting Record",
            "total_games": analysis_data.get("total_games", 0)
        }
        
        if analysis_data.get("total_games", 0) == 0:
            formatted_entries = [{"note": analysis_data.get("note", "No games found")}]
        else:
            all_time = analysis_data.get("all_time_record", {})
            recent = analysis_data.get("recent_record", {})
            
            formatted_entries = [
                {
                    "period": "All Time",
                    "ats_record": all_time.get("ats_record", "N/A"),
                    "ats_percentage": f"{all_time.get('ats_percentage', 0)}%",
                    "su_record": all_time.get("su_record", "N/A"),
                    "su_percentage": f"{all_time.get('su_percentage', 0)}%"
                }
            ]
            
            if recent and recent.get("games", 0) > 0:
                formatted_entries.append({
                    "period": f"Recent ({recent['games']} games)",
                    "ats_record": recent.get("ats_record", "N/A"),
                    "ats_percentage": f"{recent.get('ats_percentage', 0)}%",
                    "su_record": recent.get("su_record", "N/A")
                })
        
        return {"summary": summary, "entries": formatted_entries}
    
    elif analysis_type == "trends":
        summary = {
            "team": team_name,
            "analysis_type": "Recent Betting Trends",
            "period": analysis_data.get("analysis_period", "Unknown period")
        }
        
        overall = analysis_data.get("overall_trends", {})
        home_away = analysis_data.get("home_vs_away", {})
        
        formatted_entries = [
            {
                "category": "Overall Recent Performance",
                "ats_record": overall.get("ats_record", "N/A"),
                "ats_percentage": f"{overall.get('ats_percentage', 0)}%",
                "su_record": overall.get("su_record", "N/A"),
                "su_percentage": f"{overall.get('su_percentage', 0)}%"
            },
            {
                "category": f"Home Games ({home_away.get('home_games', 0)} games)",
                "ats_record": home_away.get("home_ats_record", "N/A"),
                "ats_percentage": f"{home_away.get('home_ats_percentage', 0)}%"
            },
            {
                "category": f"Away Games ({home_away.get('away_games', 0)} games)", 
                "ats_record": home_away.get("away_ats_record", "N/A"),
                "ats_percentage": f"{home_away.get('away_ats_percentage', 0)}%"
            }
        ]
        
        return {"summary": summary, "entries": formatted_entries}
    
    elif analysis_type == "over_under":
        summary = {
            "team": team_name,
            "analysis_type": "Over/Under Performance by Total Range",
            "total_ranges_analyzed": len([k for k, v in analysis_data.items() if isinstance(v, dict) and v.get('games', 0) > 0])
        }
        
        formatted_entries = []
        for range_key, range_data in analysis_data.items():
            if isinstance(range_data, dict) and range_data.get('games', 0) > 0:
                entry = {
                    "total_range": range_data["display_name"],
                    "games_played": range_data["games"],
                    "over_record": range_data["over_record"],
                    "over_percentage": f"{range_data['over_percentage']}%",
                    "under_percentage": f"{range_data['under_percentage']}%"
                }
                formatted_entries.append(entry)
        
        return {"summary": summary, "entries": formatted_entries}
    
    else:
        # For 'all' type, combine multiple analyses
        return {
            "summary": {
                "team": team_name,
                "analysis_type": "Complete Betting Analysis",
                "note": "Multiple analysis types combined"
            },
            "entries": [{"note": "Combined analysis results"}]
        }


def calculate_betting_analysis_from_graphql(graphql_result: str, team_id: int = None) -> Dict[str, Any]:
    """
    Calculate betting analysis from a GraphQL response string.
    
    Args:
        graphql_result: JSON string from GraphQL betting lines query
        team_id: Team ID to analyze (for team name lookup)
        
    Returns:
        Dictionary with betting analysis or None if insufficient data
    """
    try:
        data = json.loads(graphql_result)
        games = data.get('data', {}).get('game', [])
        
        if not games or not team_id:
            return None
            
        # Get team name from first game
        team_name = None
        for game in games:
            home_team_info = game.get('homeTeamInfo', {})
            away_team_info = game.get('awayTeamInfo', {})
            
            if home_team_info.get('teamId') == team_id:
                team_name = home_team_info.get('school')
                break
            elif away_team_info.get('teamId') == team_id:
                team_name = away_team_info.get('school')
                break
        
        if not team_name:
            return None
            
        # Calculate betting record using existing function
        betting_record = calculate_team_betting_record(games, team_name)
        
        # Add per-game details
        game_details = []
        for game in games:
            if not all([
                game.get('homePoints') is not None,
                game.get('awayPoints') is not None,
                game.get('lines') and len(game['lines']) > 0,
                game['lines'][0].get('spread') is not None
            ]):
                continue
                
            home_points = safe_numeric_conversion(game['homePoints'])
            away_points = safe_numeric_conversion(game['awayPoints'])
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            line = game['lines'][0]  # Use first betting line
            spread = safe_numeric_conversion(line['spread'])
            over_under = line.get('overUnder')
            
            # Determine opponent and game result
            team_lower = team_name.lower()
            is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
            
            if is_home_team:
                opponent = away_team
                team_score = home_points
                opponent_score = away_points
                spread_text = f"{spread:+.1f}" if spread != 0 else "PK"
            else:
                opponent = home_team
                team_score = away_points
                opponent_score = home_points
                spread_text = f"{-spread:+.1f}" if spread != 0 else "PK"
            
            # Calculate outcomes
            ats_covered = calculate_ats_outcome(home_points, away_points, spread, team_name, home_team, away_team)
            ou_over = calculate_ou_outcome(home_points, away_points, over_under) if over_under else None
            su_won = team_score > opponent_score
            
            # Format result
            result = "W" if su_won else "L"
            game_details.append({
                "opponent": opponent,
                "result": f"{result} {team_score}-{opponent_score}",
                "spread": spread_text,
                "ats_result": "Covered" if ats_covered else "Did not cover",
                "over_under": over_under,
                "ou_result": f"Over ({home_points + away_points} > {over_under})" if ou_over else f"Under ({home_points + away_points} < {over_under})" if over_under else "No line",
                "week": game.get('week'),
                "season": game.get('season')
            })
        
        return {
            "summary": betting_record,
            "game_details": game_details
        }
        
    except Exception as e:
        return {"error": f"Error calculating betting analysis: {str(e)}"}


def analyze_elo_betting_edge(
    home_elo: int, 
    away_elo: int, 
    spread: float, 
    home_team: str, 
    away_team: str
) -> Dict[str, Any]:
    """
    Analyze betting edge using ELO ratings vs betting spreads.
    
    ELO ratings predict point spreads. Compare actual spread to ELO-implied spread
    to find value bets.
    
    Args:
        home_elo: Home team ELO rating
        away_elo: Away team ELO rating  
        spread: Actual betting spread (negative = home favored)
        home_team: Home team name
        away_team: Away team name
        
    Returns:
        Dictionary with betting edge analysis
    """
    if not all([home_elo, away_elo, spread is not None]):
        return {"error": "Missing ELO or spread data"}
        
    # ELO difference predicts margin (roughly 1 ELO point = 0.03 points on spread)
    elo_diff = home_elo - away_elo
    elo_implied_spread = elo_diff * 0.03  # ELO differential to point spread conversion
    
    # Add home field advantage (typically ~3 points)
    elo_implied_spread += 3
    
    # Calculate betting edge
    spread_difference = elo_implied_spread - (-spread)  # Negative because spread is negative when home favored
    
    # Interpretation
    edge_analysis = {
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_advantage": f"{home_team} +{elo_diff}" if elo_diff > 0 else f"{away_team} +{abs(elo_diff)}",
        "elo_implied_spread": round(elo_implied_spread, 1),
        "actual_spread": spread,
        "edge_magnitude": round(abs(spread_difference), 1),
        "betting_recommendation": {}
    }
    
    if abs(spread_difference) >= 3:  # Significant edge threshold
        if spread_difference > 0:
            # ELO thinks home team is better than spread suggests
            edge_analysis["betting_recommendation"] = {
                "side": home_team,
                "confidence": "High" if abs(spread_difference) >= 5 else "Medium",
                "reasoning": f"ELO model suggests {home_team} should be favored by {elo_implied_spread:.1f}, but spread is only {spread}. {abs(spread_difference):.1f} point value on {home_team}."
            }
        else:
            # ELO thinks away team is better than spread suggests  
            edge_analysis["betting_recommendation"] = {
                "side": away_team,
                "confidence": "High" if abs(spread_difference) >= 5 else "Medium", 
                "reasoning": f"ELO model suggests {home_team} should be favored by only {elo_implied_spread:.1f}, but spread is {spread}. {abs(spread_difference):.1f} point value on {away_team}."
            }
    else:
        edge_analysis["betting_recommendation"] = {
            "side": "No strong lean",
            "confidence": "Low",
            "reasoning": f"ELO model aligns closely with betting spread. Edge of only {abs(spread_difference):.1f} points."
        }
    
    return edge_analysis


def analyze_win_probability_edge(
    home_win_prob: float,
    away_win_prob: float, 
    home_moneyline: int,
    away_moneyline: int,
    home_team: str,
    away_team: str
) -> Dict[str, Any]:
    """
    Analyze moneyline betting edge using win probabilities.
    
    Compare model win probabilities to implied probabilities from moneylines
    to find value bets.
    
    Args:
        home_win_prob: Model's home team win probability (0-1)
        away_win_prob: Model's away team win probability (0-1)
        home_moneyline: Home team moneyline (American odds)
        away_moneyline: Away team moneyline (American odds)
        home_team: Home team name
        away_team: Away team name
        
    Returns:
        Dictionary with moneyline edge analysis
    """
    if not all([home_win_prob, away_win_prob, home_moneyline, away_moneyline]):
        return {"error": "Missing win probability or moneyline data"}
        
    def american_odds_to_probability(odds):
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    # Convert moneylines to implied probabilities
    home_implied_prob = american_odds_to_probability(home_moneyline)
    away_implied_prob = american_odds_to_probability(away_moneyline)
    
    # Calculate edges
    home_edge = home_win_prob - home_implied_prob
    away_edge = away_win_prob - away_implied_prob
    
    edge_analysis = {
        "model_probabilities": {
            "home_win_prob": f"{home_win_prob:.1%}",
            "away_win_prob": f"{away_win_prob:.1%}"
        },
        "market_probabilities": {
            "home_implied_prob": f"{home_implied_prob:.1%}",
            "away_implied_prob": f"{away_implied_prob:.1%}"
        },
        "edge_analysis": {
            "home_edge": f"{home_edge:+.1%}",
            "away_edge": f"{away_edge:+.1%}"
        },
        "betting_recommendation": {}
    }
    
    # Determine best bet (minimum 5% edge for recommendation)
    min_edge_threshold = 0.05
    
    if home_edge >= min_edge_threshold and home_edge > away_edge:
        confidence = "High" if home_edge >= 0.10 else "Medium"
        edge_analysis["betting_recommendation"] = {
            "side": f"{home_team} moneyline",
            "confidence": confidence,
            "expected_value": f"+{home_edge:.1%}",
            "reasoning": f"Model gives {home_team} {home_win_prob:.1%} chance to win, but moneyline implies only {home_implied_prob:.1%}. {home_edge:+.1%} edge."
        }
    elif away_edge >= min_edge_threshold and away_edge > home_edge:
        confidence = "High" if away_edge >= 0.10 else "Medium"
        edge_analysis["betting_recommendation"] = {
            "side": f"{away_team} moneyline", 
            "confidence": confidence,
            "expected_value": f"+{away_edge:.1%}",
            "reasoning": f"Model gives {away_team} {away_win_prob:.1%} chance to win, but moneyline implies only {away_implied_prob:.1%}. {away_edge:+.1%} edge."
        }
    else:
        edge_analysis["betting_recommendation"] = {
            "side": "No strong lean",
            "confidence": "Low",
            "expected_value": f"Max edge: {max(home_edge, away_edge):+.1%}",
            "reasoning": "Neither side shows sufficient edge. Model probabilities align closely with market."
        }
        
    return edge_analysis


def interpret_advanced_metrics_for_betting(
    team_metrics: Dict[str, Any],
    opponent_metrics: Dict[str, Any], 
    game_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Interpret advanced team metrics for betting insights.
    
    Analyze offensive/defensive efficiency metrics to predict game flow,
    pace, and total scoring for betting purposes.
    
    Args:
        team_metrics: Team's advanced metrics (EPA, success rates, etc.)
        opponent_metrics: Opponent's advanced metrics
        game_context: Game context (weather, venue, etc.)
        
    Returns:
        Dictionary with betting insights from metrics
    """
    insights = {
        "offensive_matchup": {},
        "defensive_matchup": {},
        "pace_and_total_analysis": {},
        "betting_implications": {}
    }
    
    # Offensive vs Defensive EPA analysis
    team_off_epa = team_metrics.get('epa', 0)
    team_def_epa_allowed = team_metrics.get('epaAllowed', 0)
    opp_off_epa = opponent_metrics.get('epa', 0)
    opp_def_epa_allowed = opponent_metrics.get('epaAllowed', 0)
    
    # Team offense vs opponent defense
    off_vs_def_advantage = team_off_epa - opp_def_epa_allowed
    def_vs_off_advantage = team_def_epa_allowed - opp_off_epa
    
    insights["offensive_matchup"] = {
        "team_offense_epa": team_off_epa,
        "opponent_defense_epa_allowed": opp_def_epa_allowed,
        "matchup_advantage": round(off_vs_def_advantage, 3),
        "advantage_assessment": "Favorable" if off_vs_def_advantage > 0.05 else "Unfavorable" if off_vs_def_advantage < -0.05 else "Even"
    }
    
    insights["defensive_matchup"] = {
        "team_defense_epa_allowed": team_def_epa_allowed,
        "opponent_offense_epa": opp_off_epa,
        "matchup_advantage": round(def_vs_off_advantage, 3),
        "advantage_assessment": "Favorable" if def_vs_off_advantage < -0.05 else "Unfavorable" if def_vs_off_advantage > 0.05 else "Even"
    }
    
    # Pace and explosiveness for total analysis
    team_explosiveness = team_metrics.get('explosiveness', 0)
    opp_explosiveness = opponent_metrics.get('explosiveness', 0)
    combined_explosiveness = team_explosiveness + opp_explosiveness
    
    insights["pace_and_total_analysis"] = {
        "combined_explosiveness": round(combined_explosiveness, 3),
        "pace_projection": "High" if combined_explosiveness > 0.6 else "Low" if combined_explosiveness < 0.3 else "Average",
        "total_tendency": "Over lean" if combined_explosiveness > 0.5 else "Under lean" if combined_explosiveness < 0.35 else "No strong lean"
    }
    
    # Betting implications
    total_epa_advantage = off_vs_def_advantage + def_vs_off_advantage
    
    if abs(total_epa_advantage) > 0.1:
        insights["betting_implications"] = {
            "spread_lean": "Significant advantage detected",
            "confidence": "Medium to High",
            "key_factors": [
                f"{'Offensive' if off_vs_def_advantage > abs(def_vs_off_advantage) else 'Defensive'} matchup heavily favors {'team' if total_epa_advantage > 0 else 'opponent'}",
                f"Combined EPA advantage: {total_epa_advantage:+.3f}"
            ]
        }
    else:
        insights["betting_implications"] = {
            "spread_lean": "Even matchup",
            "confidence": "Low",
            "key_factors": ["Advanced metrics suggest balanced game", "Look to other factors for edge"]
        }
        
    return insights


def create_comprehensive_betting_intelligence(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create comprehensive betting intelligence by combining ELO, win probabilities, 
    and advanced metrics analysis.
    
    Args:
        game_data: Enhanced game data with ELO, win probabilities, metrics
        
    Returns:
        Dictionary with comprehensive betting intelligence
    """
    intelligence = {
        "game_overview": {
            "matchup": f"{game_data.get('awayTeam', 'Away')} @ {game_data.get('homeTeam', 'Home')}",
            "excitement_index": game_data.get('excitement'),
            "conference_game": game_data.get('conferenceGame', False)
        },
        "predictive_analysis": {},
        "betting_edges": {},
        "recommendation_summary": {}
    }
    
    # ELO Analysis
    if all([game_data.get('homeStartElo'), game_data.get('awayStartElo'), game_data.get('lines', [{}])[0].get('spread')]):
        elo_analysis = analyze_elo_betting_edge(
            game_data['homeStartElo'],
            game_data['awayStartElo'],
            game_data['lines'][0]['spread'],
            game_data.get('homeTeam', 'Home'),
            game_data.get('awayTeam', 'Away')
        )
        intelligence["predictive_analysis"]["elo_analysis"] = elo_analysis
    
    # Win Probability Analysis  
    if all([game_data.get('homePostgameWinProb'), game_data.get('awayPostgameWinProb')]):
        lines = game_data.get('lines', [{}])[0] if game_data.get('lines') else {}
        if lines.get('moneylineHome') and lines.get('moneylineAway'):
            prob_analysis = analyze_win_probability_edge(
                game_data['homePostgameWinProb'],
                game_data['awayPostgameWinProb'],
                lines['moneylineHome'],
                lines['moneylineAway'],
                game_data.get('homeTeam', 'Home'),
                game_data.get('awayTeam', 'Away')
            )
            intelligence["predictive_analysis"]["probability_analysis"] = prob_analysis
    
    # Combine recommendations
    recommendations = []
    confidence_scores = []
    
    # Extract recommendations from analyses
    for analysis_type, analysis_data in intelligence["predictive_analysis"].items():
        if isinstance(analysis_data, dict) and "betting_recommendation" in analysis_data:
            rec = analysis_data["betting_recommendation"]
            if rec.get("confidence") in ["High", "Medium"]:
                recommendations.append({
                    "source": analysis_type,
                    "recommendation": rec["side"],
                    "confidence": rec["confidence"],
                    "reasoning": rec.get("reasoning", "")
                })
                confidence_scores.append(2 if rec["confidence"] == "High" else 1)
    
    # Overall recommendation
    if recommendations:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        intelligence["recommendation_summary"] = {
            "total_analyses": len(recommendations),
            "overall_confidence": "High" if avg_confidence >= 1.5 else "Medium",
            "recommendations": recommendations,
            "consensus": "Multiple models agree" if len(set([r["recommendation"] for r in recommendations])) == 1 else "Mixed signals"
        }
    else:
        intelligence["recommendation_summary"] = {
            "total_analyses": 0,
            "overall_confidence": "Low",
            "recommendations": [],
            "consensus": "No strong betting edge detected"
        }
    
    return intelligence