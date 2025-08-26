"""
Response formatting utilities for NCAAF MCP tools.

Provides functions to format raw GraphQL responses into human-readable
summaries while optionally preserving the original data.
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


def optimize_for_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize data structure for YAML output to reduce token count.
    
    Args:
        data: Dictionary to optimize
        
    Returns:
        Optimized dictionary with unnecessary data removed
    """
    def clean_dict(obj):
        """Recursively remove null/None values and optimize data."""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = clean_dict(value)
                # Only include non-null values
                if cleaned_value is not None and cleaned_value != [] and cleaned_value != {}:
                    cleaned[key] = cleaned_value
            return cleaned
        elif isinstance(obj, list):
            return [clean_dict(item) for item in obj if item is not None]
        elif obj is None:
            return None
        else:
            return obj
    
    return clean_dict(data)


def create_formatted_response(
    raw_data: str,
    summary: Dict[str, Any],
    formatted_entries: List[Dict[str, Any]],
    include_raw_data: bool = False
) -> str:
    """
    Create a standardized formatted response structure in YAML format.
    
    Args:
        raw_data: Original JSON response from GraphQL
        summary: Summary information about the results
        formatted_entries: Human-readable data entries
        include_raw_data: Whether to include the raw GraphQL response
        
    Returns:
        YAML formatted response string (optimized for token efficiency)
    """
    response = {
        "summary": summary,
        "data": formatted_entries  # Shortened key for better compression
    }
    
    if include_raw_data:
        try:
            response["raw"] = json.loads(raw_data)  # Shortened key
        except json.JSONDecodeError:
            response["raw"] = {"error": "Could not parse raw data"}
    
    # Optimize for YAML output (remove nulls, clean up data)
    optimized_response = optimize_for_yaml(response)
    
    # Always return YAML for optimal token efficiency
    return yaml.dump(
        optimized_response,
        default_flow_style=False,
        sort_keys=False,
        width=120,  # Wider lines = fewer line breaks = fewer tokens
        allow_unicode=True
    )


def format_teams_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format teams response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from teams query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted JSON response
    """
    try:
        data = json.loads(raw_data)
        teams = data.get("data", {}).get("currentTeams", [])
        
        # Create summary
        total_teams = len(teams)
        conferences = list(set(team.get("conference") for team in teams if team.get("conference")))
        divisions = list(set(team.get("division") for team in teams if team.get("division")))
        
        summary = {
            "total_results": total_teams,
            "description": f"Found {total_teams} teams",
            "conferences_represented": len(conferences),
            "divisions_represented": len(divisions)
        }
        
        # Create formatted entries
        formatted_entries = []
        for team in teams:
            entry = {
                "team_id": team.get("teamId"),
                "school": team.get("school"),
                "conference": team.get("conference"),
                "division": team.get("division"),
                "abbreviation": team.get("abbreviation")
            }
            formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format teams response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_games_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format games response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from games query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted JSON response
    """
    try:
        data = json.loads(raw_data)
        games = data.get("data", {}).get("game", [])
        
        # Create summary
        total_games = len(games)
        completed_games = sum(1 for game in games if game.get("status") == "completed")
        upcoming_games = total_games - completed_games
        
        # Get date range
        dates = [game.get("startDate") for game in games if game.get("startDate")]
        date_range = f"{min(dates)} to {max(dates)}" if dates else "No dates available"
        
        summary = {
            "total_results": total_games,
            "description": f"Found {total_games} games",
            "completed_games": completed_games,
            "upcoming_games": upcoming_games,
            "date_range": date_range
        }
        
        # Create formatted entries with intelligent analysis
        formatted_entries = []
        for game in games:
            home_team = game.get("homeTeamInfo") or {}
            away_team = game.get("awayTeamInfo") or {}
            
            entry = {
                "game_id": game.get("id"),
                "date": game.get("startDate"),
                "week": game.get("week"),
                "season": game.get("season"),
                "status": game.get("status"),
                "matchup": f"{away_team.get('school', 'TBD')} @ {home_team.get('school', 'TBD')}",
                "score": f"{game.get('awayPoints', 0)} - {game.get('homePoints', 0)}" if game.get("status") == "completed" else "TBD"
            }
            
            # Add predictive analytics if available
            predictive_data = {}
            
            # ELO Analysis
            home_elo = game.get("homeStartElo")
            away_elo = game.get("awayStartElo") 
            if home_elo and away_elo:
                elo_diff = home_elo - away_elo
                predictive_data["elo_analysis"] = {
                    "home_elo": home_elo,
                    "away_elo": away_elo,
                    "elo_advantage": f"{home_team.get('school', 'Home')} +{elo_diff}" if elo_diff > 0 else f"{away_team.get('school', 'Away')} +{abs(elo_diff)}",
                    "elo_implied_spread": round(elo_diff * 0.03 + 3, 1),  # ELO to spread conversion + HFA
                    "strength_assessment": "Elite Matchup" if min(home_elo, away_elo) > 1900 else "Strong Teams" if min(home_elo, away_elo) > 1700 else "Average Teams"
                }
            
            # Win Probability Analysis
            home_win_prob = game.get("homePostgameWinProb")
            away_win_prob = game.get("awayPostgameWinProb")
            if home_win_prob is not None and away_win_prob is not None:
                predictive_data["win_probabilities"] = {
                    "home_win_prob": f"{home_win_prob:.1%}",
                    "away_win_prob": f"{away_win_prob:.1%}",
                    "model_favorite": home_team.get('school', 'Home') if home_win_prob > away_win_prob else away_team.get('school', 'Away'),
                    "confidence_level": "High" if max(home_win_prob, away_win_prob) > 0.7 else "Medium" if max(home_win_prob, away_win_prob) > 0.6 else "Low"
                }
            
            # Game Context
            excitement = game.get("excitement")
            if excitement is not None:
                predictive_data["game_context"] = {
                    "excitement_index": round(excitement, 2),
                    "excitement_level": "Extremely High" if excitement > 8 else "High" if excitement > 6 else "Medium" if excitement > 4 else "Low",
                    "conference_game": game.get("conferenceGame", False),
                    "neutral_site": game.get("neutralSite", False)
                }
            
            # Line Scores for completed games
            if game.get("status") == "completed":
                home_line_scores = game.get("homeLineScores")
                away_line_scores = game.get("awayLineScores")
                if home_line_scores and away_line_scores:
                    predictive_data["scoring_flow"] = {
                        "home_by_quarter": home_line_scores,
                        "away_by_quarter": away_line_scores,
                        "total_quarters": len(home_line_scores),
                        "overtime": len(home_line_scores) > 4
                    }
            
            # Add predictive analysis to entry if any data available
            if predictive_data:
                entry["predictive_analysis"] = predictive_data
            
            formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format games response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_betting_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format betting lines response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from betting query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted JSON response
    """
    try:
        data = json.loads(raw_data)
        
        # Check if betting summary exists (from calculate_records=true)
        if "betting_summary" in data:
            games = data.get("data", {}).get("game", [])
            betting_summary = data.get("betting_summary", {})
            
            # Enhanced summary with betting analysis
            enhanced_summary = {
                "total_results": len(games),
                "description": f"Found {len(games)} games with betting analysis",
                "ats_record": betting_summary.get("ats", "N/A"),
                "ats_percentage": betting_summary.get("ats_percentage", 0),
                "ou_record": betting_summary.get("ou", "N/A"),
                "ou_percentage": betting_summary.get("ou_percentage", 0),
                "su_record": betting_summary.get("su", "N/A"),
                "su_percentage": betting_summary.get("su_percentage", 0)
            }
            
            # Create formatted entries from the raw games data
            formatted_entries = []
            for game in games:
                if not all([
                    game.get('homePoints') is not None,
                    game.get('awayPoints') is not None,
                    game.get('lines') and len(game['lines']) > 0
                ]):
                    continue
                    
                home_team_info = game.get('homeTeamInfo') or {}
                away_team_info = game.get('awayTeamInfo') or {}
                line = game['lines'][0]  # Use first betting line
                
                # Determine which team we're analyzing (based on betting_summary context)
                # This is a simplified approach - the detailed analysis logic is in betting_utils
                entry = {
                    "opponent": away_team_info.get('school', 'TBD'),  # Simplified
                    "result": f"{'W' if game.get('homePoints', 0) > game.get('awayPoints', 0) else 'L'} {game.get('homePoints', 0)}-{game.get('awayPoints', 0)}",
                    "spread": str(line.get('spread', 0)),
                    "over_under": line.get('overUnder'),
                    "week": game.get('week'),
                    "season": game.get('season')
                }
                formatted_entries.append(entry)
            
            return create_formatted_response(raw_data, enhanced_summary, formatted_entries, include_raw_data)
        
        # Fall back to basic formatting if no betting analysis
        games = data.get("data", {}).get("game", [])
        
        # Create summary
        total_games = len(games)
        games_with_lines = sum(1 for game in games if game.get("lines"))
        
        spreads = []
        totals = []
        
        for game in games:
            lines = game.get("lines", [])
            for line in lines:
                if line.get("spread") is not None:
                    spreads.append(abs(line.get("spread")))
                if line.get("overUnder") is not None:
                    totals.append(line.get("overUnder"))
        
        avg_spread = sum(spreads) / len(spreads) if spreads else 0
        avg_total = sum(totals) / len(totals) if totals else 0
        
        summary = {
            "total_results": total_games,
            "description": f"Found {total_games} games with betting data",
            "games_with_lines": games_with_lines,
            "average_spread": round(avg_spread, 1),
            "average_total": round(avg_total, 1)
        }
        
        # Create formatted entries with intelligent betting analysis
        formatted_entries = []
        for game in games:
            home_team = game.get("homeTeamInfo") or {}
            away_team = game.get("awayTeamInfo") or {}
            lines = game.get("lines", [])
            
            line_info = "No lines available"
            if lines:
                line = lines[0]  # Take first line
                spread = line.get("spread")
                total = line.get("overUnder")
                
                spread_text = f"Spread: {spread}" if spread is not None else "No spread"
                total_text = f"O/U: {total}" if total is not None else "No total"
                line_info = f"{spread_text}, {total_text}"
            
            entry = {
                "game_id": game.get("id"),
                "date": game.get("startDate"),
                "matchup": f"{away_team.get('school', 'TBD')} @ {home_team.get('school', 'TBD')}",
                "betting_lines": line_info,
                "status": game.get("status")
            }
            
            # Add intelligent betting analysis if predictive data is available
            betting_intelligence = {}
            
            # ELO Betting Edge Analysis
            home_elo = game.get("homeStartElo")
            away_elo = game.get("awayStartElo") 
            if home_elo and away_elo and lines:
                line = lines[0]
                spread = line.get("spread")
                if spread is not None:
                    elo_diff = home_elo - away_elo
                    elo_implied_spread = elo_diff * 0.03 + 3  # Convert ELO to spread + HFA
                    spread_difference = elo_implied_spread - (-spread)  # Negative because spread is negative when home favored
                    
                    betting_intelligence["elo_edge_analysis"] = {
                        "elo_implied_spread": round(elo_implied_spread, 1),
                        "actual_spread": spread,
                        "edge_magnitude": round(abs(spread_difference), 1),
                        "value_side": home_team.get('school', 'Home') if spread_difference > 0 else away_team.get('school', 'Away'),
                        "edge_assessment": "Strong Value" if abs(spread_difference) >= 3 else "Moderate Value" if abs(spread_difference) >= 1.5 else "No Significant Edge"
                    }
            
            # Win Probability vs Moneyline Analysis
            home_win_prob = game.get("homePostgameWinProb")
            away_win_prob = game.get("awayPostgameWinProb")
            if home_win_prob is not None and away_win_prob is not None and lines:
                line = lines[0] 
                home_ml = line.get("moneylineHome")
                away_ml = line.get("moneylineAway")
                
                if home_ml and away_ml:
                    # Convert American odds to implied probability
                    def american_odds_to_prob(odds):
                        if odds > 0:
                            return 100 / (odds + 100)
                        else:
                            return abs(odds) / (abs(odds) + 100)
                    
                    home_implied_prob = american_odds_to_prob(home_ml)
                    away_implied_prob = american_odds_to_prob(away_ml)
                    
                    home_edge = home_win_prob - home_implied_prob
                    away_edge = away_win_prob - away_implied_prob
                    
                    best_edge = max(home_edge, away_edge)
                    if best_edge >= 0.05:  # 5% edge threshold
                        betting_intelligence["moneyline_value"] = {
                            "best_value_team": home_team.get('school', 'Home') if home_edge > away_edge else away_team.get('school', 'Away'),
                            "expected_value": f"+{best_edge:.1%}",
                            "model_prob": f"{home_win_prob:.1%}" if home_edge > away_edge else f"{away_win_prob:.1%}",
                            "market_prob": f"{home_implied_prob:.1%}" if home_edge > away_edge else f"{away_implied_prob:.1%}",
                            "value_assessment": "Excellent Value" if best_edge >= 0.10 else "Good Value"
                        }
            
            # Game Context for Betting
            excitement = game.get("excitement")
            if excitement is not None:
                betting_intelligence["game_context"] = {
                    "excitement_level": "Extremely High" if excitement > 8 else "High" if excitement > 6 else "Medium" if excitement > 4 else "Low",
                    "betting_popularity": "Public will be heavily on this game" if excitement > 7 else "Moderate public interest" if excitement > 5 else "Lower public interest",
                    "conference_rivalry": game.get("conferenceGame", False),
                    "neutral_site": game.get("neutralSite", False)
                }
            
            # Add betting intelligence if any analysis available
            if betting_intelligence:
                entry["betting_intelligence"] = betting_intelligence
            
            formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format betting response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_rankings_response(raw_data: str, include_raw_data: bool = False, context: dict = None) -> str:
    """
    Format rankings response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from rankings query
        include_raw_data: Whether to include raw data
        context: Additional context for formatting (poll_type, team, movement, top_n)
        
    Returns:
        Formatted YAML response optimized for single poll or team search
    """
    try:
        data = json.loads(raw_data)
        polls = data.get("data", {}).get("poll", [])
        previous_week_data = data.get("previous_week_data", {})
        
        # Extract context parameters
        context = context or {}
        poll_type = context.get('poll_type')
        team = context.get('team')
        movement = context.get('movement', False)
        top_n = context.get('top_n', 25)
        
        # Prepare movement data if available
        prev_rankings = {}
        if movement and previous_week_data:
            prev_polls = previous_week_data.get("poll", [])
            for prev_poll in prev_polls:
                for prev_ranking in prev_poll.get("rankings", []):
                    school = prev_ranking.get("team", {}).get("school")
                    if school:
                        prev_rankings[school] = prev_ranking.get("rank")
        
        # Handle team-specific search across all polls
        if team:
            team_rankings = []
            for poll in polls:
                poll_name = poll.get("pollType", {}).get("name", "Unknown Poll")
                rankings = poll.get("rankings", [])
                
                for ranking in rankings:
                    team_obj = ranking.get("team", {})
                    team_info = {
                        "poll": poll_name,
                        "rank": ranking.get("rank"),
                        "school": team_obj.get("school"),
                        "conference": team_obj.get("conference"),
                        "points": ranking.get("points"),
                        "first_place_votes": ranking.get("firstPlaceVotes", 0)
                    }
                    
                    # Add movement indicator
                    if movement:
                        prev_rank = prev_rankings.get(team_obj.get("school"))
                        if prev_rank:
                            rank_change = prev_rank - ranking.get("rank")
                            if rank_change > 0:
                                team_info["movement"] = f"↑{rank_change}"
                            elif rank_change < 0:
                                team_info["movement"] = f"↓{abs(rank_change)}"
                            else:
                                team_info["movement"] = "→"
                    
                    team_rankings.append(team_info)
            
            summary = {
                "search_term": team,
                "season": polls[0].get("season") if polls else None,
                "week": polls[0].get("week") if polls else None,
                "found_in_polls": len(team_rankings)
            }
            
            return create_formatted_response(raw_data, summary, {"team_rankings": team_rankings}, include_raw_data)
        
        # Handle single poll display with full Top 25
        elif len(polls) == 1:
            poll = polls[0]
            poll_name = poll.get("pollType", {}).get("name", "Unknown Poll")
            rankings = poll.get("rankings", [])
            
            formatted_teams = []
            for i, ranking in enumerate(rankings[:top_n], 1):
                team_obj = ranking.get("team", {})
                rank = ranking.get("rank", i)
                school = team_obj.get("school", "Unknown")
                conference = team_obj.get("conference", "")
                points = ranking.get("points")
                fpv = ranking.get("firstPlaceVotes", 0)
                
                # Format team entry
                team_str = f"{rank}. {school}"
                if conference:
                    team_str += f" ({conference})"
                
                # Add first place votes for top teams
                if fpv > 0:
                    team_str += f" ({fpv})"
                
                # Add points if available
                if points and points > 0:
                    team_str += f" - {points} pts"
                
                # Add movement indicator
                if movement:
                    prev_rank = prev_rankings.get(school)
                    if prev_rank:
                        rank_change = prev_rank - rank
                        if rank_change > 0:
                            team_str += f" (↑{rank_change})"
                        elif rank_change < 0:
                            team_str += f" (↓{abs(rank_change)})"
                        else:
                            team_str += " (→)"
                
                formatted_teams.append(team_str)
            
            summary = {
                "poll_name": poll_name,
                "season": poll.get("season"),
                "week": poll.get("week"),
                "teams_shown": len(formatted_teams)
            }
            
            return create_formatted_response(raw_data, summary, {"rankings": formatted_teams}, include_raw_data)
        
        # Handle multiple polls (fallback to original format)
        else:
            total_polls = len(polls)
            all_rankings = []
            poll_types = set()
            
            for poll in polls:
                poll_types.add(poll.get("pollType", {}).get("name", "Unknown"))
                rankings = poll.get("rankings", [])
                all_rankings.extend(rankings)
            
            summary = {
                "total_results": len(all_rankings),
                "description": f"Found {len(all_rankings)} team rankings across {total_polls} polls",
                "poll_types": list(poll_types),
                "season": polls[0].get("season") if polls else None,
                "week": polls[0].get("week") if polls else None
            }
            
            formatted_entries = []
            for poll in polls:
                poll_name = poll.get("pollType", {}).get("name", "Unknown Poll")
                rankings = poll.get("rankings", [])
                
                poll_entry = {
                    "poll_name": poll_name,
                    "season": poll.get("season"),
                    "week": poll.get("week"),
                    "top_teams": []
                }
                
                # Show limited teams for multiple polls
                for ranking in rankings[:10]:
                    team = ranking.get("team", {})
                    team_info = {
                        "rank": ranking.get("rank"),
                        "school": team.get("school"),
                        "conference": team.get("conference"),
                        "points": ranking.get("points"),
                        "first_place_votes": ranking.get("firstPlaceVotes", 0)
                    }
                    poll_entry["top_teams"].append(team_info)
                
                formatted_entries.append(poll_entry)
            
            return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format rankings response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_athletes_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format athletes response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from athletes query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted JSON response
    """
    try:
        data = json.loads(raw_data)
        athletes = data.get("data", {}).get("athlete", [])
        
        # Create summary
        total_athletes = len(athletes)
        positions = {}
        teams = set()
        
        for athlete in athletes:
            # Count by position (assuming positionId corresponds to position)
            pos_id = athlete.get("positionId")
            if pos_id:
                positions[pos_id] = positions.get(pos_id, 0) + 1
            
            # Collect teams
            athlete_teams = athlete.get("athleteTeams", [])
            for team in athlete_teams:
                team_info = team.get("team", {})
                if team_info.get("school"):
                    teams.add(team_info.get("school"))
        
        summary = {
            "total_results": total_athletes,
            "description": f"Found {total_athletes} athletes",
            "teams_represented": len(teams),
            "position_distribution": positions
        }
        
        # Create formatted entries
        formatted_entries = []
        for athlete in athletes:
            team_info = ""
            athlete_teams = athlete.get("athleteTeams", [])
            if athlete_teams:
                team = athlete_teams[0].get("team", {})
                team_info = team.get("school", "Unknown")
            
            entry = {
                "athlete_id": athlete.get("id"),
                "name": athlete.get("name"),
                "jersey": athlete.get("jersey"),
                "position": athlete.get("positionId"),
                "height": athlete.get("height"),
                "weight": athlete.get("weight"),
                "team": team_info
            }
            formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format athletes response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_depth_chart_response(raw_data: str, include_raw_data: bool = False, context: dict = None) -> str:
    """
    Format depth chart response into organized team depth chart.
    
    Args:
        raw_data: Raw JSON response from depth chart query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted YAML response with organized depth chart
    """
    try:
        data = json.loads(raw_data)
        athletes = data.get("data", {}).get("athlete", [])
        
        if not athletes:
            return create_formatted_response(raw_data, {"description": "No players found"}, [], include_raw_data)
        
        # Get team info from first player
        team_info = athletes[0].get("athleteTeams", [{}])[0].get("team", {})
        team_name = team_info.get("school", "Unknown Team")
        
        # Position mapping for organization
        position_groups = {
            # Offense
            "Quarterback": {"group": "offense", "positions": ["QB"], "depth": 3},
            "Running Back": {"group": "offense", "positions": ["RB", "FB"], "depth": 4},
            "Wide Receiver": {"group": "offense", "positions": ["WR"], "depth": 6},
            "Tight End": {"group": "offense", "positions": ["TE"], "depth": 3},
            "Offensive Lineman": {"group": "offense", "positions": ["OL", "OT", "OG", "C"], "depth": 8},
            
            # Defense  
            "Defensive Lineman": {"group": "defense", "positions": ["DL", "DE", "NT"], "depth": 6},
            "Defensive Tackle": {"group": "defense", "positions": ["DT"], "depth": 4},
            "Defensive End": {"group": "defense", "positions": ["DE"], "depth": 4},
            "Linebacker": {"group": "defense", "positions": ["LB", "ILB", "OLB", "MLB"], "depth": 6},
            "Cornerback": {"group": "defense", "positions": ["CB"], "depth": 4},
            "Safety": {"group": "defense", "positions": ["S", "SS", "FS"], "depth": 4},
            "Defensive Back": {"group": "defense", "positions": ["DB"], "depth": 4},
            
            # Special Teams
            "Place kicker": {"group": "special_teams", "positions": ["PK", "K"], "depth": 2},
            "Punter": {"group": "special_teams", "positions": ["P"], "depth": 2},
            "Long Snapper": {"group": "special_teams", "positions": ["LS"], "depth": 2},
        }
        
        # Group players by position
        position_players = {}
        for athlete in athletes:
            position = athlete.get("position")
            if not position:
                continue
                
            pos_name = position.get("name", "Unknown")
            pos_abbr = position.get("abbreviation", "")
            
            if pos_name not in position_players:
                position_players[pos_name] = []
                
            # Calculate class year based on athleteTeams years
            class_year = "Sr"  # Default
            athlete_teams = athlete.get("athleteTeams", [])
            if athlete_teams:
                start_year = athlete_teams[0].get("startYear")
                end_year = athlete_teams[0].get("endYear") 
                if start_year and end_year:
                    years_played = end_year - start_year + 1
                    if years_played == 1:
                        class_year = "Fr"
                    elif years_played == 2:
                        class_year = "So"
                    elif years_played == 3:
                        class_year = "Jr"
                    elif years_played >= 4:
                        class_year = "Sr"
            
            player_info = {
                "name": athlete.get("name", "Unknown"),
                "jersey": athlete.get("jersey"),
                "height": athlete.get("height"),
                "weight": athlete.get("weight"),
                "class_year": class_year,
                "position_abbr": pos_abbr
            }
            
            position_players[pos_name].append(player_info)
        
        # Extract filter parameters from context
        context = context or {}
        offensive_only = context.get('offensive_only', False)
        defensive_only = context.get('defensive_only', False)
        include_special_teams = context.get('include_special_teams', True)
        
        # Organize into depth chart
        depth_chart = {"offense": {}, "defense": {}, "special_teams": {}}
        
        for pos_name, players in position_players.items():
            if pos_name in position_groups:
                group_info = position_groups[pos_name]
                group = group_info["group"]
                max_depth = group_info["depth"]
                
                # Apply filtering logic
                if offensive_only and group != "offense":
                    continue
                if defensive_only and group != "defense":
                    continue
                if not include_special_teams and group == "special_teams":
                    continue
                
                # Sort players by jersey number (lower numbers typically starters)
                players_sorted = sorted(players, key=lambda p: p.get("jersey") or 99)
                
                # Take only the number we want for depth chart
                depth_players = players_sorted[:max_depth]
                
                # Format position display
                if depth_players:
                    formatted_players = []
                    for i, player in enumerate(depth_players):
                        jersey = f"#{player['jersey']}" if player['jersey'] else ""
                        name = player['name']
                        class_yr = player['class_year']
                        height = f"{player['height']//12}'{player['height']%12}\"" if player['height'] else ""
                        weight = f"{player['weight']}lbs" if player['weight'] else ""
                        
                        # Create player string
                        player_str = f"{name} ({jersey}, {class_yr})"
                        if height and weight:
                            player_str += f" - {height}, {weight}"
                        
                        formatted_players.append(player_str)
                    
                    # Use position abbreviation if available, otherwise position name
                    pos_key = players[0]['position_abbr'] or pos_name
                    depth_chart[group][pos_key] = formatted_players
        
        # Create summary
        total_players = sum(len(players) for players in depth_chart.values() for players in players.values())
        
        summary = {
            "team": team_name,
            "total_players": total_players,
            "description": f"Depth chart for {team_name} showing key players by position",
            "offense_positions": len(depth_chart["offense"]),
            "defense_positions": len(depth_chart["defense"]),
            "special_teams_positions": len(depth_chart["special_teams"])
        }
        
        return create_formatted_response(raw_data, summary, depth_chart, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format depth chart response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_metrics_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format advanced metrics response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from metrics query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted JSON response
    """
    try:
        data = json.loads(raw_data)
        
        # This is a generic formatter since metrics structure may vary
        # Extract top-level data arrays
        metrics_data = []
        for key, value in data.get("data", {}).items():
            if isinstance(value, list):
                metrics_data.extend(value)
        
        summary = {
            "total_results": len(metrics_data),
            "description": f"Found {len(metrics_data)} metric entries",
            "data_types": list(data.get("data", {}).keys())
        }
        
        # Create formatted entries (generic approach)
        formatted_entries = []
        for item in metrics_data[:20]:  # Limit to first 20 for readability
            if isinstance(item, dict):
                # Extract key fields that are commonly useful
                entry = {}
                for field in ['teamId', 'team', 'school', 'season', 'week', 'value', 'metric', 'category']:
                    if field in item:
                        entry[field] = item[field]
                formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format metrics response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_team_ratings_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format team ratings response into human-readable YAML summary with intelligent analysis.
    
    Args:
        raw_data: Raw JSON response from team ratings query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted YAML response with intelligent ratings analysis
    """
    try:
        data = json.loads(raw_data)
        team_data = data.get("data", {}).get("team_ratings", {})
        
        ratings = team_data.get("ratings", [])
        talent = team_data.get("talent", [])
        team_id = team_data.get("team_id")
        season = team_data.get("season")
        
        if not ratings:
            summary = {
                "team_id": team_id,
                "season": season,
                "description": "No ratings data found for this team/season",
                "available_data": "None"
            }
            return create_formatted_response(raw_data, summary, [], include_raw_data)
        
        rating = ratings[0]  # Get first (primary) rating
        talent_data = talent[0] if talent else {}
        
        # Create intelligent summary
        summary = {
            "team": rating.get("team"),
            "conference": rating.get("conference"),
            "season": season,
            "overall_strength": "Elite" if rating.get("elo", 0) > 1900 else "Strong" if rating.get("elo", 0) > 1700 else "Average" if rating.get("elo", 0) > 1500 else "Below Average",
            "key_metrics": {
                "elo_rating": rating.get("elo"),
                "fpi_overall": rating.get("fpi"),
                "sp_plus_overall": rating.get("spOverall"),
                "srs_rating": rating.get("srs"),
                "talent_composite": talent_data.get("talent") if talent_data else None
            }
        }
        
        # Create formatted entries with intelligent analysis
        formatted_entries = []
        
        # Overall Strength Analysis
        formatted_entries.append({
            "category": "Overall Team Strength",
            "elo_rating": rating.get("elo"),
            "elo_interpretation": "Elite (Top 10)" if rating.get("elo", 0) > 1900 else "Strong (Top 25)" if rating.get("elo", 0) > 1700 else "Average" if rating.get("elo", 0) > 1500 else "Below Average",
            "fpi_overall": rating.get("fpi"),
            "sp_plus_overall": rating.get("spOverall"),
            "srs_rating": rating.get("srs")
        })
        
        # Efficiency Breakdown
        formatted_entries.append({
            "category": "Efficiency Ratings (FPI)",
            "offensive_efficiency": rating.get("fpiOffensiveEfficiency"),
            "defensive_efficiency": rating.get("fpiDefensiveEfficiency"),
            "special_teams_efficiency": rating.get("fpiSpecialTeamsEfficiency"),
            "overall_efficiency": rating.get("fpiOverallEfficiency"),
            "efficiency_balance": "Offensive" if (rating.get("fpiOffensiveEfficiency", 50) - rating.get("fpiDefensiveEfficiency", 50)) > 10 else "Defensive" if (rating.get("fpiDefensiveEfficiency", 50) - rating.get("fpiOffensiveEfficiency", 50)) > 10 else "Balanced"
        })
        
        # SP+ Breakdown
        formatted_entries.append({
            "category": "SP+ Unit Ratings",
            "sp_offense": rating.get("spOffense"),
            "sp_defense": rating.get("spDefense"), 
            "sp_special_teams": rating.get("spSpecialTeams"),
            "sp_overall": rating.get("spOverall"),
            "dominant_unit": "Offense" if (rating.get("spOffense", 0) - abs(rating.get("spDefense", 0))) > 5 else "Defense" if (abs(rating.get("spDefense", 0)) - rating.get("spOffense", 0)) > 5 else "Balanced"
        })
        
        # Schedule and Context
        formatted_entries.append({
            "category": "Schedule & Context",
            "strength_of_schedule_rank": rating.get("fpiSosRank"),
            "resume_rank": rating.get("fpiResumeRank"),
            "strength_of_record_rank": rating.get("fpiStrengthOfRecordRank"),
            "game_control_rank": rating.get("fpiGameControlRank"),
            "schedule_difficulty": "Extremely Hard" if rating.get("fpiSosRank", 100) <= 10 else "Hard" if rating.get("fpiSosRank", 100) <= 30 else "Average" if rating.get("fpiSosRank", 100) <= 70 else "Easy"
        })
        
        # Talent Analysis
        if talent_data:
            formatted_entries.append({
                "category": "Talent Composite",
                "talent_rating": talent_data.get("talent"),
                "talent_level": "Elite" if talent_data.get("talent", 0) > 900 else "High" if talent_data.get("talent", 0) > 800 else "Above Average" if talent_data.get("talent", 0) > 700 else "Average",
                "recruiting_strength": "Top 10 class equivalent" if talent_data.get("talent", 0) > 950 else "Top 25 class equivalent" if talent_data.get("talent", 0) > 850 else "Solid recruiting" if talent_data.get("talent", 0) > 750 else "Average recruiting"
            })
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format team ratings response: {str(e)}",
            "raw_data": json.loads(raw_data) if raw_data else None
        }, indent=2)


def format_generic_graphql_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format generic GraphQL response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from GraphQL query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted YAML response
    """
    try:
        data = json.loads(raw_data)
        
        # Handle GraphQL response structure
        graphql_data = data.get("data", {})
        errors = data.get("errors", [])
        
        # Create summary
        total_fields = len(graphql_data.keys())
        total_items = 0
        field_info = {}
        
        for field_name, field_data in graphql_data.items():
            if isinstance(field_data, list):
                field_count = len(field_data)
                total_items += field_count
                field_info[field_name] = {
                    "type": "array",
                    "count": field_count,
                    "sample_keys": list(field_data[0].keys())[:5] if field_data and isinstance(field_data[0], dict) else []
                }
            elif isinstance(field_data, dict):
                field_info[field_name] = {
                    "type": "object", 
                    "keys": list(field_data.keys())[:5]
                }
                total_items += 1
            else:
                field_info[field_name] = {
                    "type": type(field_data).__name__,
                    "value": field_data
                }
                total_items += 1
        
        summary = {
            "total_results": total_items,
            "description": f"GraphQL query returned {total_fields} fields with {total_items} total items",
            "fields_returned": list(graphql_data.keys()),
            "field_details": field_info
        }
        
        if errors:
            summary["errors"] = errors
        
        # Create formatted entries - flatten the response for better readability
        formatted_entries = []
        
        for field_name, field_data in graphql_data.items():
            if isinstance(field_data, list):
                # Show first 10 items from arrays
                for i, item in enumerate(field_data[:10]):
                    entry = {
                        "field": field_name,
                        "index": i,
                        "data": item
                    }
                    formatted_entries.append(entry)
            else:
                # Single objects or values
                entry = {
                    "field": field_name,
                    "data": field_data
                }
                formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format generic GraphQL response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def safe_format_response(
    raw_data: str, 
    response_type: str, 
    include_raw_data: bool = False,
    context: dict = None
) -> str:
    """
    Safely format response with fallback to raw data on error.
    Always returns YAML format for optimal token efficiency.
    
    Args:
        raw_data: Raw JSON response
        response_type: Type of response (teams, games, betting, rankings, athletes, metrics, generic)
        include_raw_data: Whether to include raw data
        context: Additional context for formatting
        
    Returns:
        YAML formatted response or raw data if formatting fails
    """
    formatters = {
        'teams': format_teams_response,
        'games': format_games_response,
        'betting': format_betting_response,
        'rankings': format_rankings_response,
        'athletes': format_athletes_response,
        'depth_chart': format_depth_chart_response,
        'metrics': format_metrics_response,
        'team_ratings': format_team_ratings_response,
        'generic': format_generic_graphql_response
    }
    
    formatter = formatters.get(response_type)
    if formatter:
        try:
            if response_type in ['rankings', 'depth_chart'] and context:
                return formatter(raw_data, include_raw_data, context)
            else:
                return formatter(raw_data, include_raw_data)
        except Exception as e:
            # Fallback to generic formatting
            try:
                return format_generic_graphql_response(raw_data, include_raw_data)
            except Exception as fallback_e:
                # Final fallback to raw data with error message
                return json.dumps({
                    "error": f"All formatting failed: {str(e)}, fallback error: {str(fallback_e)}",
                    "raw_data": json.loads(raw_data) if raw_data else None
                }, indent=2)
    else:
        # Unknown response type, use generic formatter
        return format_generic_graphql_response(raw_data, include_raw_data)