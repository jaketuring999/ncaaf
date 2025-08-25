"""
Ranking analysis utilities for college football ranking data.

Functions to calculate ranking movement, volatility, biggest movers,
and historical ranking trends from GraphQL query results.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, stdev
from collections import defaultdict


def calculate_ranking_movement(current_rankings: List[Dict[str, Any]], 
                             previous_rankings: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate week-over-week ranking movement.
    
    Args:
        current_rankings: List of current week's rankings
        previous_rankings: List of previous week's rankings (optional)
        
    Returns:
        Dictionary with ranking movement analysis
    """
    if not current_rankings:
        return {"error": "No current rankings provided"}
    
    movement_analysis = {
        "total_teams": len(current_rankings),
        "biggest_movers": {
            "up": [],
            "down": [],
            "new_entries": [],
            "dropped_out": []
        },
        "stability_metrics": {
            "teams_unchanged": 0,
            "average_movement": 0.0,
            "most_volatile_positions": []
        }
    }
    
    if not previous_rankings:
        # No previous rankings to compare
        movement_analysis["note"] = "No previous rankings available for comparison"
        return movement_analysis
    
    # Create lookup dictionaries
    current_dict = {team.get('school', ''): {
        'rank': team.get('rank', 999),
        'poll': team.get('poll', ''),
        'points': team.get('points', 0)
    } for team in current_rankings}
    
    previous_dict = {team.get('school', ''): {
        'rank': team.get('rank', 999),
        'poll': team.get('poll', ''),
        'points': team.get('points', 0)
    } for team in previous_rankings}
    
    movements = []
    unchanged_count = 0
    
    # Calculate movements for teams in current rankings
    for team_name, current_data in current_dict.items():
        if team_name in previous_dict:
            previous_rank = previous_dict[team_name]['rank']
            current_rank = current_data['rank']
            movement = previous_rank - current_rank  # Positive = moved up, negative = moved down
            
            movements.append(abs(movement))
            
            if movement == 0:
                unchanged_count += 1
            elif movement > 0:  # Moved up
                movement_analysis["biggest_movers"]["up"].append({
                    "team": team_name,
                    "previous_rank": previous_rank,
                    "current_rank": current_rank,
                    "movement": movement,
                    "poll": current_data['poll']
                })
            else:  # Moved down
                movement_analysis["biggest_movers"]["down"].append({
                    "team": team_name,
                    "previous_rank": previous_rank,
                    "current_rank": current_rank,
                    "movement": abs(movement),
                    "poll": current_data['poll']
                })
        else:
            # New entry
            movement_analysis["biggest_movers"]["new_entries"].append({
                "team": team_name,
                "current_rank": current_data['rank'],
                "poll": current_data['poll']
            })
    
    # Find teams that dropped out
    for team_name, previous_data in previous_dict.items():
        if team_name not in current_dict:
            movement_analysis["biggest_movers"]["dropped_out"].append({
                "team": team_name,
                "previous_rank": previous_data['rank'],
                "poll": previous_data['poll']
            })
    
    # Sort biggest movers
    movement_analysis["biggest_movers"]["up"].sort(key=lambda x: x["movement"], reverse=True)
    movement_analysis["biggest_movers"]["down"].sort(key=lambda x: x["movement"], reverse=True)
    movement_analysis["biggest_movers"]["new_entries"].sort(key=lambda x: x["current_rank"])
    movement_analysis["biggest_movers"]["dropped_out"].sort(key=lambda x: x["previous_rank"])
    
    # Calculate stability metrics
    movement_analysis["stability_metrics"]["teams_unchanged"] = unchanged_count
    movement_analysis["stability_metrics"]["average_movement"] = round(mean(movements), 1) if movements else 0.0
    movement_analysis["stability_metrics"]["total_movement"] = sum(movements)
    
    return movement_analysis


def calculate_ranking_volatility(rankings_history: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate ranking volatility over multiple weeks.
    
    Args:
        rankings_history: List of ranking lists (each week's rankings)
        
    Returns:
        Dictionary with volatility analysis
    """
    if not rankings_history or len(rankings_history) < 2:
        return {"error": "Need at least 2 weeks of rankings for volatility analysis"}
    
    # Track each team's ranking positions over time
    team_rankings = defaultdict(list)
    weeks_analyzed = len(rankings_history)
    
    for week_rankings in rankings_history:
        # Create a set of teams ranked this week
        ranked_teams = set()
        for team in week_rankings:
            team_name = team.get('school', '')
            rank = team.get('rank', 999)
            team_rankings[team_name].append(rank)
            ranked_teams.add(team_name)
        
        # For teams not ranked this week, add a high number (e.g., 999)
        for team_name in team_rankings:
            if team_name not in ranked_teams:
                team_rankings[team_name].append(999)
    
    volatility_scores = []
    most_volatile = []
    most_stable = []
    
    for team_name, ranks in team_rankings.items():
        if len(ranks) >= 2:  # Need at least 2 data points
            # Filter out unranked weeks (rank 999) for standard deviation calculation
            ranked_weeks = [r for r in ranks if r != 999]
            
            if len(ranked_weeks) >= 2:
                volatility = stdev(ranked_weeks)
                avg_rank = mean(ranked_weeks)
                
                volatility_scores.append(volatility)
                
                team_analysis = {
                    "team": team_name,
                    "volatility_score": round(volatility, 2),
                    "average_rank": round(avg_rank, 1),
                    "weeks_ranked": len(ranked_weeks),
                    "best_rank": min(ranked_weeks),
                    "worst_rank": max(ranked_weeks),
                    "rank_range": max(ranked_weeks) - min(ranked_weeks)
                }
                
                if volatility > 3:  # Arbitrary threshold for high volatility
                    most_volatile.append(team_analysis)
                elif volatility < 1:  # Low volatility = stable
                    most_stable.append(team_analysis)
    
    # Sort by volatility
    most_volatile.sort(key=lambda x: x["volatility_score"], reverse=True)
    most_stable.sort(key=lambda x: x["volatility_score"])
    
    return {
        "weeks_analyzed": weeks_analyzed,
        "teams_analyzed": len(team_rankings),
        "overall_volatility": {
            "average_volatility": round(mean(volatility_scores), 2) if volatility_scores else 0.0,
            "max_volatility": round(max(volatility_scores), 2) if volatility_scores else 0.0,
            "min_volatility": round(min(volatility_scores), 2) if volatility_scores else 0.0
        },
        "most_volatile_teams": most_volatile[:5],
        "most_stable_teams": most_stable[:5]
    }


def identify_ranking_trends(rankings_history: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Identify teams with consistent upward or downward ranking trends.
    
    Args:
        rankings_history: List of ranking lists (each week's rankings)
        
    Returns:
        Dictionary with trend analysis
    """
    if not rankings_history or len(rankings_history) < 3:
        return {"error": "Need at least 3 weeks of rankings for trend analysis"}
    
    team_trends = defaultdict(list)
    
    # Collect rankings for each team
    for week_rankings in rankings_history:
        week_teams = {team.get('school', ''): team.get('rank', 999) for team in week_rankings}
        for team_name in team_trends:
            if team_name not in week_teams:
                team_trends[team_name].append(999)  # Unranked
        
        for team_name, rank in week_teams.items():
            if team_name not in team_trends:
                team_trends[team_name] = [999] * (len(rankings_history) - 1)
            team_trends[team_name].append(rank)
    
    rising_teams = []
    falling_teams = []
    consistent_teams = []
    
    for team_name, ranks in team_trends.items():
        # Filter out unranked weeks for trend calculation
        ranked_positions = [(i, rank) for i, rank in enumerate(ranks) if rank != 999]
        
        if len(ranked_positions) >= 3:  # Need at least 3 ranked weeks
            # Calculate trend (lower rank numbers are better)
            first_rank = ranked_positions[0][1]
            last_rank = ranked_positions[-1][1]
            
            # Simple trend calculation
            trend_direction = first_rank - last_rank  # Positive = improving (rank going down in number)
            weeks_tracked = len(ranked_positions)
            
            team_trend = {
                "team": team_name,
                "first_rank": first_rank,
                "last_rank": last_rank,
                "trend_value": trend_direction,
                "weeks_tracked": weeks_tracked,
                "best_rank": min([r[1] for r in ranked_positions]),
                "worst_rank": max([r[1] for r in ranked_positions])
            }
            
            if trend_direction > 2:  # Improved by more than 2 positions
                rising_teams.append(team_trend)
            elif trend_direction < -2:  # Fell by more than 2 positions
                falling_teams.append(team_trend)
            else:
                consistent_teams.append(team_trend)
    
    # Sort teams
    rising_teams.sort(key=lambda x: x["trend_value"], reverse=True)
    falling_teams.sort(key=lambda x: x["trend_value"])
    
    return {
        "weeks_analyzed": len(rankings_history),
        "rising_teams": rising_teams[:5],
        "falling_teams": falling_teams[:5],
        "most_consistent": consistent_teams[:5],
        "summary": {
            "total_rising": len(rising_teams),
            "total_falling": len(falling_teams),
            "total_consistent": len(consistent_teams)
        }
    }


def calculate_poll_consensus(rankings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze consensus between different polls (AP, Coaches, CFP, etc.).
    
    Args:
        rankings: List of rankings from potentially multiple polls
        
    Returns:
        Dictionary with poll consensus analysis
    """
    if not rankings:
        return {"error": "No rankings provided"}
    
    # Group rankings by poll
    polls = defaultdict(list)
    for ranking in rankings:
        poll_name = ranking.get('poll', 'Unknown')
        polls[poll_name].append(ranking)
    
    poll_analysis = {
        "polls_found": list(polls.keys()),
        "poll_count": len(polls),
        "consensus_analysis": {}
    }
    
    if len(polls) < 2:
        poll_analysis["note"] = "Need multiple polls for consensus analysis"
        return poll_analysis
    
    # Find teams ranked in multiple polls
    team_rankings = defaultdict(dict)
    for poll_name, poll_rankings in polls.items():
        for team in poll_rankings:
            team_name = team.get('school', '')
            rank = team.get('rank')
            if rank:
                team_rankings[team_name][poll_name] = rank
    
    consensus_teams = []
    controversial_teams = []
    
    for team_name, poll_ranks in team_rankings.items():
        if len(poll_ranks) >= 2:  # Ranked in at least 2 polls
            ranks = list(poll_ranks.values())
            avg_rank = mean(ranks)
            rank_spread = max(ranks) - min(ranks)
            
            team_consensus = {
                "team": team_name,
                "average_rank": round(avg_rank, 1),
                "rank_spread": rank_spread,
                "poll_rankings": poll_ranks,
                "polls_ranked_in": len(poll_ranks)
            }
            
            if rank_spread <= 2:  # Close consensus
                consensus_teams.append(team_consensus)
            elif rank_spread >= 5:  # High disagreement
                controversial_teams.append(team_consensus)
    
    # Sort by average rank
    consensus_teams.sort(key=lambda x: x["average_rank"])
    controversial_teams.sort(key=lambda x: x["rank_spread"], reverse=True)
    
    poll_analysis["consensus_analysis"] = {
        "strong_consensus": consensus_teams[:10],
        "controversial_rankings": controversial_teams[:5],
        "teams_in_multiple_polls": len(team_rankings)
    }
    
    return poll_analysis


def calculate_ranking_movement_from_graphql(graphql_result: str, 
                                          previous_graphql_result: str = None) -> Dict[str, Any]:
    """
    Calculate ranking movement analysis from GraphQL response strings.
    
    Args:
        graphql_result: JSON string from current week's GraphQL rankings query
        previous_graphql_result: JSON string from previous week's rankings (optional)
        
    Returns:
        Dictionary with ranking movement analysis
    """
    try:
        current_data = json.loads(graphql_result)
        current_rankings = current_data.get('data', {}).get('rankings', [])
        
        if not current_rankings:
            return {"error": "No current rankings found in response"}
        
        previous_rankings = None
        if previous_graphql_result:
            try:
                previous_data = json.loads(previous_graphql_result)
                previous_rankings = previous_data.get('data', {}).get('rankings', [])
            except:
                pass  # Ignore errors in previous rankings
        
        # Calculate movement analysis
        movement_analysis = calculate_ranking_movement(current_rankings, previous_rankings)
        
        # Add poll consensus analysis for current rankings
        consensus_analysis = calculate_poll_consensus(current_rankings)
        
        return {
            "current_week_analysis": movement_analysis,
            "poll_consensus": consensus_analysis,
            "metadata": {
                "current_rankings_count": len(current_rankings),
                "previous_rankings_available": previous_rankings is not None,
                "previous_rankings_count": len(previous_rankings) if previous_rankings else 0
            }
        }
        
    except Exception as e:
        return {"error": f"Error calculating ranking movement: {str(e)}"}