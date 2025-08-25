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
    total_points = home_points + away_points
    return total_points > over_under


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
            
        home_points = game['homePoints']
        away_points = game['awayPoints']
        home_team = game.get('homeTeam', '')
        away_team = game.get('awayTeam', '')
        
        # Get betting lines (use first line if multiple)
        line = game['lines'][0]
        spread = line['spread']
        over_under = line.get('overUnder')
        
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
            
        home_points = game['homePoints']
        away_points = game['awayPoints']
        line = game['lines'][0]
        spread = line.get('spread')
        over_under = line.get('overUnder')
        
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
                
            home_points = game['homePoints']
            away_points = game['awayPoints']
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            line = game['lines'][0]  # Use first betting line
            spread = line['spread']
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