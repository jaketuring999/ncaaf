"""
Game analysis utilities for college football game data.

Functions to calculate scoring trends, upset analysis, momentum shifts,
and weekly game statistics from GraphQL query results.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, median


def calculate_scoring_trends(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate scoring trends and patterns from a list of games.
    
    Args:
        games: List of game dictionaries from GraphQL query
        
    Returns:
        Dictionary with scoring trend analysis
    """
    if not games:
        return {"error": "No games provided"}
    
    total_scores = []
    home_scores = []
    away_scores = []
    margins = []
    completed_games = 0
    
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None):
            
            home_pts = game['homePoints']
            away_pts = game['awayPoints']
            total = home_pts + away_pts
            margin = abs(home_pts - away_pts)
            
            total_scores.append(total)
            home_scores.append(home_pts)
            away_scores.append(away_pts)
            margins.append(margin)
            completed_games += 1
    
    if completed_games == 0:
        return {"error": "No completed games found"}
    
    return {
        "games_analyzed": completed_games,
        "total_points": {
            "average": round(mean(total_scores), 1),
            "median": median(total_scores),
            "highest": max(total_scores),
            "lowest": min(total_scores)
        },
        "home_team_scoring": {
            "average": round(mean(home_scores), 1),
            "median": median(home_scores)
        },
        "away_team_scoring": {
            "average": round(mean(away_scores), 1),
            "median": median(away_scores)
        },
        "margins": {
            "average_margin": round(mean(margins), 1),
            "median_margin": median(margins),
            "blowouts_20plus": len([m for m in margins if m >= 20]),
            "one_score_games": len([m for m in margins if m <= 7])
        }
    }


def calculate_upset_analysis(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze upsets based on betting lines (when favorites lose).
    
    Args:
        games: List of game dictionaries with betting lines
        
    Returns:
        Dictionary with upset analysis
    """
    if not games:
        return {"error": "No games provided"}
    
    upsets = []
    favorites_analysis = []
    games_with_lines = 0
    
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None and
            game.get('lines') and len(game['lines']) > 0):
            
            home_pts = game['homePoints']
            away_pts = game['awayPoints']
            line = game['lines'][0]  # Use first betting line
            spread = line.get('spread')
            
            if spread is None:
                continue
                
            games_with_lines += 1
            home_team = game.get('homeTeam', 'Home')
            away_team = game.get('awayTeam', 'Away')
            margin = home_pts - away_pts
            
            # Determine favorite and if they covered
            if spread < 0:  # Home team favored
                favorite = home_team
                favorite_won = margin > 0
                favorite_covered = margin > abs(spread)
                underdog = away_team
            else:  # Away team favored
                favorite = away_team
                favorite_won = margin < 0
                favorite_covered = -margin > spread
                underdog = home_team
            
            favorites_analysis.append({
                "favorite": favorite,
                "won": favorite_won,
                "covered": favorite_covered
            })
            
            # Check for upsets (favorite lost straight up)
            if not favorite_won:
                upsets.append({
                    "favorite": favorite,
                    "underdog": underdog,
                    "spread": spread,
                    "final_score": f"{home_team} {home_pts}, {away_team} {away_pts}",
                    "upset_margin": abs(margin)
                })
    
    if games_with_lines == 0:
        return {"error": "No games with betting lines found"}
    
    favorites_won = len([f for f in favorites_analysis if f["won"]])
    favorites_covered = len([f for f in favorites_analysis if f["covered"]])
    
    return {
        "games_analyzed": games_with_lines,
        "upsets": {
            "total_upsets": len(upsets),
            "upset_details": upsets[:5],  # Limit to first 5 for readability
            "upset_rate": round(len(upsets) / games_with_lines * 100, 1)
        },
        "favorites_performance": {
            "won_straight_up": f"{favorites_won}-{games_with_lines - favorites_won}",
            "covered_spread": f"{favorites_covered}-{games_with_lines - favorites_covered}",
            "win_percentage": round(favorites_won / games_with_lines * 100, 1),
            "cover_percentage": round(favorites_covered / games_with_lines * 100, 1)
        }
    }


def calculate_weekly_trends(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate weekly betting and scoring trends.
    
    Args:
        games: List of games for a specific week
        
    Returns:
        Dictionary with weekly trend analysis
    """
    if not games:
        return {"error": "No games provided"}
    
    # Reuse existing functions and add weekly-specific metrics
    scoring_trends = calculate_scoring_trends(games)
    upset_analysis = calculate_upset_analysis(games)
    
    # Additional weekly-specific analysis
    over_under_analysis = []
    games_with_totals = 0
    
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None and
            game.get('lines') and len(game['lines']) > 0):
            
            line = game['lines'][0]
            over_under = line.get('overUnder')
            
            if over_under is not None:
                total_points = game['homePoints'] + game['awayPoints']
                went_over = total_points > over_under
                over_under_analysis.append({
                    "total_points": total_points,
                    "over_under": over_under,
                    "went_over": went_over
                })
                games_with_totals += 1
    
    overs_hit = len([ou for ou in over_under_analysis if ou["went_over"]])
    
    weekly_summary = {
        "week_overview": {
            "total_games": len(games),
            "completed_games": scoring_trends.get("games_analyzed", 0)
        },
        "scoring": scoring_trends,
        "upsets": upset_analysis,
        "over_under": {
            "games_with_totals": games_with_totals,
            "overs_hit": overs_hit,
            "unders_hit": games_with_totals - overs_hit,
            "over_percentage": round(overs_hit / games_with_totals * 100, 1) if games_with_totals > 0 else 0.0
        }
    }
    
    return weekly_summary


def calculate_game_stats_from_graphql(graphql_result: str, analysis_type: str = "trends") -> Dict[str, Any]:
    """
    Calculate game statistics from a GraphQL response string.
    
    Args:
        graphql_result: JSON string from GraphQL games query
        analysis_type: Type of analysis - "trends", "upsets", "weekly"
        
    Returns:
        Dictionary with game analysis or None if insufficient data
    """
    try:
        data = json.loads(graphql_result)
        games = data.get('data', {}).get('game', [])
        
        if not games:
            return {"error": "No games found in response"}
        
        if analysis_type == "trends":
            return calculate_scoring_trends(games)
        elif analysis_type == "upsets":
            return calculate_upset_analysis(games)
        elif analysis_type == "weekly":
            return calculate_weekly_trends(games)
        else:
            # Default: return comprehensive analysis
            return {
                "scoring_trends": calculate_scoring_trends(games),
                "upset_analysis": calculate_upset_analysis(games)
            }
            
    except Exception as e:
        return {"error": f"Error calculating game statistics: {str(e)}"}


def identify_notable_games(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify notable games (upsets, high-scoring, close games, etc.).
    
    Args:
        games: List of game dictionaries
        
    Returns:
        Dictionary with notable games categorized
    """
    if not games:
        return {"error": "No games provided"}
    
    notable_games = {
        "high_scoring": [],
        "low_scoring": [],
        "close_games": [],
        "blowouts": [],
        "overtime_games": []
    }
    
    total_scores = []
    margins = []
    
    # First pass: collect data for thresholds
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None):
            
            total_points = game['homePoints'] + game['awayPoints']
            margin = abs(game['homePoints'] - game['awayPoints'])
            
            total_scores.append(total_points)
            margins.append(margin)
    
    if not total_scores:
        return {"error": "No completed games found"}
    
    # Calculate thresholds
    avg_total = mean(total_scores)
    high_scoring_threshold = avg_total + 20  # 20 points above average
    low_scoring_threshold = avg_total - 20   # 20 points below average
    
    # Second pass: categorize games
    for game in games:
        if (game.get('status') == 'completed' and 
            game.get('homePoints') is not None and 
            game.get('awayPoints') is not None):
            
            home_pts = game['homePoints']
            away_pts = game['awayPoints']
            total_points = home_pts + away_pts
            margin = abs(home_pts - away_pts)
            
            game_summary = {
                "matchup": f"{game.get('awayTeam', 'Away')} @ {game.get('homeTeam', 'Home')}",
                "score": f"{away_pts}-{home_pts}",
                "total_points": total_points,
                "margin": margin,
                "week": game.get('week'),
                "date": game.get('startDate')
            }
            
            # Categorize
            if total_points >= high_scoring_threshold:
                notable_games["high_scoring"].append(game_summary)
            elif total_points <= low_scoring_threshold:
                notable_games["low_scoring"].append(game_summary)
                
            if margin <= 3:
                notable_games["close_games"].append(game_summary)
            elif margin >= 28:
                notable_games["blowouts"].append(game_summary)
                
            # Check for overtime (this would need to be in the data)
            if game.get('status') == 'completed' and 'OT' in str(game.get('notes', '')):
                notable_games["overtime_games"].append(game_summary)
    
    # Sort and limit results
    for category in notable_games:
        if category == "high_scoring":
            notable_games[category] = sorted(notable_games[category], 
                                           key=lambda x: x["total_points"], reverse=True)[:5]
        elif category == "close_games":
            notable_games[category] = sorted(notable_games[category], 
                                           key=lambda x: x["margin"])[:5]
        else:
            notable_games[category] = notable_games[category][:5]
    
    return notable_games