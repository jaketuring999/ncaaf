"""
Team performance analysis utilities for college football team data.

Functions to calculate team performance metrics, home/away splits,
conference records, streak analysis, and season summaries.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean
from datetime import datetime


def calculate_team_performance_splits(games: List[Dict[str, Any]], team_name: str) -> Dict[str, Any]:
    """
    Calculate home/away and conference/non-conference performance splits.
    
    Args:
        games: List of game dictionaries for a specific team
        team_name: Name of the team to analyze
        
    Returns:
        Dictionary with performance split analysis
    """
    if not games:
        return {"error": "No games provided"}
    
    home_games = {"wins": 0, "losses": 0, "points_for": 0, "points_against": 0}
    away_games = {"wins": 0, "losses": 0, "points_for": 0, "points_against": 0}
    conference_games = {"wins": 0, "losses": 0, "points_for": 0, "points_against": 0}
    non_conf_games = {"wins": 0, "losses": 0, "points_for": 0, "points_against": 0}
    
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None):
            
            home_pts = game['homePoints']
            away_pts = game['awayPoints']
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            
            # Determine if team is home or away
            team_lower = team_name.lower()
            is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
            
            if is_home_team:
                team_points = home_pts
                opponent_points = away_pts
                game_location = home_games
            else:
                team_points = away_pts
                opponent_points = home_pts
                game_location = away_games
            
            # Record win/loss and points
            if team_points > opponent_points:
                game_location["wins"] += 1
            else:
                game_location["losses"] += 1
            
            game_location["points_for"] += team_points
            game_location["points_against"] += opponent_points
            
            # Determine conference vs non-conference
            home_team_info = game.get('homeTeamInfo', {})
            away_team_info = game.get('awayTeamInfo', {})
            
            if is_home_team:
                team_conf = home_team_info.get('conference', '')
                opponent_conf = away_team_info.get('conference', '')
            else:
                team_conf = away_team_info.get('conference', '')
                opponent_conf = home_team_info.get('conference', '')
            
            # Check if it's a conference game
            is_conference_game = (team_conf and opponent_conf and 
                                team_conf.lower() == opponent_conf.lower() and
                                team_conf.lower() not in ['fbs independents', 'independent'])
            
            if is_conference_game:
                conf_split = conference_games
            else:
                conf_split = non_conf_games
            
            if team_points > opponent_points:
                conf_split["wins"] += 1
            else:
                conf_split["losses"] += 1
            
            conf_split["points_for"] += team_points
            conf_split["points_against"] += opponent_points
    
    def format_split_stats(split_data: Dict) -> Dict:
        total_games = split_data["wins"] + split_data["losses"]
        return {
            "record": f"{split_data['wins']}-{split_data['losses']}",
            "win_percentage": round(split_data["wins"] / total_games * 100, 1) if total_games > 0 else 0.0,
            "points_per_game": round(split_data["points_for"] / total_games, 1) if total_games > 0 else 0.0,
            "points_allowed_per_game": round(split_data["points_against"] / total_games, 1) if total_games > 0 else 0.0,
            "point_differential": round((split_data["points_for"] - split_data["points_against"]) / total_games, 1) if total_games > 0 else 0.0
        }
    
    return {
        "team": team_name,
        "home_performance": format_split_stats(home_games),
        "away_performance": format_split_stats(away_games),
        "conference_performance": format_split_stats(conference_games),
        "non_conference_performance": format_split_stats(non_conf_games)
    }


def calculate_streak_analysis(games: List[Dict[str, Any]], team_name: str) -> Dict[str, Any]:
    """
    Calculate current win/loss streaks and close game performance.
    
    Args:
        games: List of game dictionaries for a specific team (should be in chronological order)
        team_name: Name of the team to analyze
        
    Returns:
        Dictionary with streak analysis
    """
    if not games:
        return {"error": "No games provided"}
    
    # Sort games by date (most recent first for streak calculation)
    completed_games = []
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None):
            completed_games.append(game)
    
    # Sort by start date, most recent first
    completed_games.sort(key=lambda x: x.get('startDate', ''), reverse=True)
    
    if not completed_games:
        return {"error": "No completed games found"}
    
    # Calculate current streak
    current_streak = ""
    streak_count = 0
    last_result = None
    
    close_games = {"wins": 0, "losses": 0}  # Games decided by 7 points or less
    blowout_games = {"wins": 0, "losses": 0}  # Games decided by 21+ points
    
    for game in completed_games:
        home_pts = game['homePoints']
        away_pts = game['awayPoints']
        home_team = game.get('homeTeam', '')
        away_team = game.get('awayTeam', '')
        
        # Determine if team won
        team_lower = team_name.lower()
        is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
        
        if is_home_team:
            team_points = home_pts
            opponent_points = away_pts
        else:
            team_points = away_pts
            opponent_points = home_pts
        
        won_game = team_points > opponent_points
        margin = abs(team_points - opponent_points)
        
        # Close game analysis (7 points or less)
        if margin <= 7:
            if won_game:
                close_games["wins"] += 1
            else:
                close_games["losses"] += 1
        
        # Blowout analysis (21+ points)
        if margin >= 21:
            if won_game:
                blowout_games["wins"] += 1
            else:
                blowout_games["losses"] += 1
        
        # Current streak calculation (only for most recent games)
        if last_result is None:
            last_result = "W" if won_game else "L"
            streak_count = 1
        elif (won_game and last_result == "W") or (not won_game and last_result == "L"):
            streak_count += 1
        else:
            break  # Streak ended
    
    current_streak = f"{last_result}{streak_count}" if last_result else "No games"
    
    return {
        "team": team_name,
        "current_streak": current_streak,
        "close_game_record": f"{close_games['wins']}-{close_games['losses']}",
        "close_game_percentage": round(close_games["wins"] / (close_games["wins"] + close_games["losses"]) * 100, 1) if (close_games["wins"] + close_games["losses"]) > 0 else 0.0,
        "blowout_record": f"{blowout_games['wins']}-{blowout_games['losses']}",
        "blowout_percentage": round(blowout_games["wins"] / (blowout_games["wins"] + blowout_games["losses"]) * 100, 1) if (blowout_games["wins"] + blowout_games["losses"]) > 0 else 0.0,
        "total_games_analyzed": len(completed_games)
    }


def calculate_season_summary(games: List[Dict[str, Any]], team_name: str, team_id: int = None) -> Dict[str, Any]:
    """
    Calculate comprehensive season summary for a team.
    
    Args:
        games: List of game dictionaries for a specific team
        team_name: Name of the team to analyze
        team_id: Team ID for additional context
        
    Returns:
        Dictionary with season summary
    """
    if not games:
        return {"error": "No games provided"}
    
    wins = 0
    losses = 0
    total_points_for = 0
    total_points_against = 0
    completed_games = 0
    
    best_win = None
    worst_loss = None
    highest_scoring = None
    lowest_scoring = None
    
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None):
            
            home_pts = game['homePoints']
            away_pts = game['awayPoints']
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            
            # Determine team's performance
            team_lower = team_name.lower()
            is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
            
            if is_home_team:
                team_points = home_pts
                opponent_points = away_pts
                opponent_name = away_team
            else:
                team_points = away_pts
                opponent_points = home_pts
                opponent_name = home_team
            
            completed_games += 1
            total_points_for += team_points
            total_points_against += opponent_points
            
            game_summary = {
                "opponent": opponent_name,
                "score": f"{team_points}-{opponent_points}",
                "location": "vs" if is_home_team else "@",
                "margin": team_points - opponent_points,
                "week": game.get('week'),
                "date": game.get('startDate')
            }
            
            if team_points > opponent_points:
                wins += 1
                # Check if this is the best win (by margin or opponent quality)
                if best_win is None or game_summary["margin"] > best_win["margin"]:
                    best_win = game_summary
            else:
                losses += 1
                # Check if this is the worst loss
                if worst_loss is None or game_summary["margin"] < worst_loss["margin"]:
                    worst_loss = game_summary
            
            # Track highest and lowest scoring games
            if highest_scoring is None or team_points > highest_scoring["team_points"]:
                highest_scoring = {**game_summary, "team_points": team_points}
            
            if lowest_scoring is None or team_points < lowest_scoring["team_points"]:
                lowest_scoring = {**game_summary, "team_points": team_points}
    
    if completed_games == 0:
        return {"error": "No completed games found"}
    
    # Get performance splits and streaks
    performance_splits = calculate_team_performance_splits(games, team_name)
    streak_analysis = calculate_streak_analysis(games, team_name)
    
    return {
        "team": team_name,
        "season_record": f"{wins}-{losses}",
        "win_percentage": round(wins / completed_games * 100, 1),
        "scoring": {
            "points_per_game": round(total_points_for / completed_games, 1),
            "points_allowed_per_game": round(total_points_against / completed_games, 1),
            "point_differential_per_game": round((total_points_for - total_points_against) / completed_games, 1),
            "total_points_for": total_points_for,
            "total_points_against": total_points_against
        },
        "notable_games": {
            "best_win": best_win,
            "worst_loss": worst_loss,
            "highest_scoring": highest_scoring,
            "lowest_scoring": lowest_scoring
        },
        "performance_splits": performance_splits,
        "streak_analysis": streak_analysis,
        "games_played": completed_games
    }


def calculate_team_performance_from_graphql(graphql_result: str, team_id: int = None) -> Dict[str, Any]:
    """
    Calculate team performance analysis from a GraphQL response string.
    
    Args:
        graphql_result: JSON string from GraphQL team games query
        team_id: Team ID to analyze (for team name lookup)
        
    Returns:
        Dictionary with team performance analysis or None if insufficient data
    """
    try:
        data = json.loads(graphql_result)
        games = data.get('data', {}).get('game', [])
        
        if not games:
            return {"error": "No games found in response"}
        
        # Get team name from first game
        team_name = None
        for game in games:
            home_team_info = game.get('homeTeamInfo', {})
            away_team_info = game.get('awayTeamInfo', {})
            
            if team_id:
                if home_team_info.get('teamId') == team_id:
                    team_name = home_team_info.get('school')
                    break
                elif away_team_info.get('teamId') == team_id:
                    team_name = away_team_info.get('school')
                    break
            else:
                # If no team_id provided, try to infer from the first game
                team_name = home_team_info.get('school') or away_team_info.get('school')
                break
        
        if not team_name:
            return {"error": "Could not determine team name from games"}
        
        # Calculate comprehensive team performance
        season_summary = calculate_season_summary(games, team_name, team_id)
        
        return season_summary
        
    except Exception as e:
        return {"error": f"Error calculating team performance: {str(e)}"}


def calculate_strength_of_schedule(games: List[Dict[str, Any]], team_name: str) -> Dict[str, Any]:
    """
    Calculate basic strength of schedule metrics.
    
    Args:
        games: List of game dictionaries for a specific team
        team_name: Name of the team to analyze
        
    Returns:
        Dictionary with strength of schedule analysis
    """
    if not games:
        return {"error": "No games provided"}
    
    opponents = []
    conference_opponents = 0
    ranked_opponents = 0  # This would need ranking data
    
    for game in games:
        if game.get('status') == 'completed':
            home_team = game.get('homeTeam', '')
            away_team = game.get('awayTeam', '')
            
            # Determine opponent
            team_lower = team_name.lower()
            is_home_team = team_lower in home_team.lower() or home_team.lower() in team_lower
            
            if is_home_team:
                opponent = away_team
                opponent_info = game.get('awayTeamInfo', {})
            else:
                opponent = home_team
                opponent_info = game.get('homeTeamInfo', {})
            
            opponents.append({
                "name": opponent,
                "conference": opponent_info.get('conference', 'Unknown')
            })
            
            # Count conference games
            team_info = game.get('homeTeamInfo' if is_home_team else 'awayTeamInfo', {})
            team_conf = team_info.get('conference', '')
            opponent_conf = opponent_info.get('conference', '')
            
            if (team_conf and opponent_conf and 
                team_conf.lower() == opponent_conf.lower() and
                team_conf.lower() not in ['fbs independents', 'independent']):
                conference_opponents += 1
    
    unique_conferences = len(set(opp['conference'] for opp in opponents if opp['conference'] != 'Unknown'))
    
    return {
        "team": team_name,
        "total_opponents": len(opponents),
        "conference_games": conference_opponents,
        "non_conference_games": len(opponents) - conference_opponents,
        "conferences_faced": unique_conferences,
        "opponents": [opp["name"] for opp in opponents]
    }