"""
Response formatting utilities for NCAAF MCP tools.

Provides functions to format raw GraphQL responses into human-readable
summaries while optionally preserving the original data.
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


def create_formatted_response(
    raw_data: str,
    summary: Dict[str, Any],
    formatted_entries: List[Dict[str, Any]],
    include_raw_data: bool = False
) -> str:
    """
    Create a standardized formatted response structure.
    
    Args:
        raw_data: Original JSON response from GraphQL
        summary: Summary information about the results
        formatted_entries: Human-readable data entries
        include_raw_data: Whether to include the raw GraphQL response
        
    Returns:
        JSON string with formatted response
    """
    response = {
        "summary": summary,
        "formatted_data": formatted_entries
    }
    
    if include_raw_data:
        try:
            response["raw_data"] = json.loads(raw_data)
        except json.JSONDecodeError:
            response["raw_data"] = {"error": "Could not parse raw data"}
    
    return json.dumps(response, indent=2)


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
        
        # Create formatted entries
        formatted_entries = []
        for game in games:
            home_team = game.get("homeTeamInfo", {})
            away_team = game.get("awayTeamInfo", {})
            
            entry = {
                "game_id": game.get("id"),
                "date": game.get("startDate"),
                "week": game.get("week"),
                "season": game.get("season"),
                "status": game.get("status"),
                "matchup": f"{away_team.get('school', 'TBD')} @ {home_team.get('school', 'TBD')}",
                "score": f"{game.get('awayPoints', 0)} - {game.get('homePoints', 0)}" if game.get("status") == "completed" else "TBD"
            }
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
        
        # Check if betting analysis already exists (from calculate_records=true)
        if "betting_analysis" in data:
            games = data.get("data", {}).get("game", [])
            betting_analysis = data.get("betting_analysis", {})
            
            # Enhanced summary with betting analysis
            summary = betting_analysis.get("summary", {})
            enhanced_summary = {
                "total_results": len(games),
                "description": f"Found {len(games)} games with betting analysis",
                "ats_record": summary.get("ats", "N/A"),
                "ats_percentage": summary.get("ats_percentage", 0),
                "ou_record": summary.get("ou", "N/A"),
                "ou_percentage": summary.get("ou_percentage", 0),
                "su_record": summary.get("su", "N/A"),
                "su_percentage": summary.get("su_percentage", 0)
            }
            
            # Use the detailed game analysis
            formatted_entries = betting_analysis.get("game_details", [])
            
            # Create response with betting analysis
            response = {
                "summary": enhanced_summary,
                "formatted_data": formatted_entries,
                "betting_analysis": betting_analysis
            }
            
            if include_raw_data:
                response["raw_data"] = data
            
            return json.dumps(response, indent=2)
        
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
        
        # Create formatted entries
        formatted_entries = []
        for game in games:
            home_team = game.get("homeTeamInfo", {})
            away_team = game.get("awayTeamInfo", {})
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
            formatted_entries.append(entry)
        
        return create_formatted_response(raw_data, summary, formatted_entries, include_raw_data)
        
    except Exception as e:
        return json.dumps({
            "error": f"Failed to format betting response: {str(e)}",
            "raw_data": raw_data if include_raw_data else None
        }, indent=2)


def format_rankings_response(raw_data: str, include_raw_data: bool = False) -> str:
    """
    Format rankings response into human-readable summary.
    
    Args:
        raw_data: Raw JSON response from rankings query
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted JSON response
    """
    try:
        data = json.loads(raw_data)
        polls = data.get("data", {}).get("poll", [])
        
        # Create summary
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
        
        # Create formatted entries - show top 25 teams
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
            
            # Show top 10 teams
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


def safe_format_response(
    raw_data: str, 
    response_type: str, 
    include_raw_data: bool = False
) -> str:
    """
    Safely format response with fallback to raw data on error.
    
    Args:
        raw_data: Raw JSON response
        response_type: Type of response (teams, games, betting, rankings, athletes, metrics)
        include_raw_data: Whether to include raw data
        
    Returns:
        Formatted response or raw data if formatting fails
    """
    formatters = {
        'teams': format_teams_response,
        'games': format_games_response,
        'betting': format_betting_response,
        'rankings': format_rankings_response,
        'athletes': format_athletes_response,
        'metrics': format_metrics_response
    }
    
    formatter = formatters.get(response_type)
    if formatter:
        try:
            return formatter(raw_data, include_raw_data)
        except Exception as e:
            # Fallback to raw data with error message
            return json.dumps({
                "error": f"Formatting failed for {response_type}: {str(e)}",
                "raw_data": json.loads(raw_data) if raw_data else None
            }, indent=2)
    else:
        # Unknown response type, return raw data
        return raw_data