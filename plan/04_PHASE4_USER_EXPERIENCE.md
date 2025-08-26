# Phase 4: User Experience Improvements

## Overview
Make the MCP tools more intuitive and natural to use by improving parameter inference, defaults, and response quality. Focus on reducing friction between user intent and tool selection.

## UX Improvements

### 4.1 Smart Parameter Inference (Priority: HIGH)
**Goal**: Tools should understand context and infer missing parameters intelligently.

#### Current Season Awareness
```python
# utils/season_helper.py
from datetime import datetime

def get_current_season():
    """Intelligently determine current season based on date"""
    now = datetime.now()
    # If January-July, use previous year (looking at last season)
    # If August-December, use current year (current season)
    if now.month <= 7:
        return now.year - 1
    return now.year

def get_current_week():
    """Determine current week of season"""
    # Week 0: Last week of August
    # Week 1: First week of September
    # Calculate based on date
    pass
```

#### Implementation in Tools
```python
@mcp.tool()
async def GetGames(
    season: Optional[Union[str, int]] = None,  # Auto-defaults to current
    week: Optional[Union[str, int]] = None,    # Auto-defaults to current
    ...
) -> str:
    # Smart defaults
    if season is None:
        season = get_current_season()
    if week is None and season == get_current_season():
        week = get_current_week()
```

### 4.2 Natural Language Team Resolution (Priority: HIGH)
**Goal**: Accept any reasonable way to reference a team.

#### Team Resolver Enhancement
```python
# utils/team_resolver.py

TEAM_ALIASES = {
    # Full names
    "University of Alabama": "Alabama",
    "Ohio State University": "Ohio State",
    "Louisiana State University": "LSU",
    
    # Common nicknames
    "Bama": "Alabama",
    "tOSU": "Ohio State", 
    "The U": "Miami",
    "Ole Miss": "Mississippi",
    
    # Cities
    "Columbus": "Ohio State",
    "Tuscaloosa": "Alabama",
    "Ann Arbor": "Michigan",
    
    # Mascots
    "Crimson Tide": "Alabama",
    "Buckeyes": "Ohio State",
    "Wolverines": "Michigan",
    "Tigers": ["LSU", "Auburn", "Clemson"],  # Needs context
    
    # Abbreviations
    "OSU": ["Ohio State", "Oklahoma State", "Oregon State"],  # Needs context
    "MSU": ["Michigan State", "Mississippi State"],
    "UM": ["Michigan", "Miami"],
    
    # Phonetic/Misspellings
    "Mishigan": "Michigan",
    "Ahia State": "Ohio State",
}

async def resolve_team(
    team_input: str,
    context: Optional[Dict] = None
) -> str:
    """Resolve team name with context awareness"""
    # Check exact match first
    # Then check aliases
    # Use context for disambiguation (conference, state, recent mentions)
    # Fuzzy matching as fallback
```

### 4.3 Conversational Memory (Priority: MEDIUM)
**Goal**: Remember context from previous queries in conversation.

#### Context Manager
```python
# utils/context_manager.py

class ConversationContext:
    def __init__(self):
        self.recent_teams = []
        self.current_season = None
        self.current_week = None
        self.conference_focus = None
        
    def update_from_query(self, params):
        """Update context based on query parameters"""
        if 'team' in params:
            self.recent_teams.append(params['team'])
        if 'season' in params:
            self.current_season = params['season']
            
    def infer_params(self, params):
        """Fill missing params from context"""
        if not params.get('team') and self.recent_teams:
            params['team'] = self.recent_teams[-1]
        if not params.get('season'):
            params['season'] = self.current_season
        return params
```

### 4.4 Enhanced Tool Descriptions (Priority: HIGH)
**Goal**: Help LLM select the right tool for user queries.

#### Improved Docstrings
```python
@mcp.tool()
async def GetGames(...) -> str:
    """Get college football games with smart filtering and insights.
    
    BEST FOR:
    - "What games are on this week?" → Returns current week's games
    - "Show me ranked matchups" → Filters to games with ranked teams
    - "Most exciting games" → Sorted by excitement index
    - "Conference games only" → Use conference_game filter
    
    NOT FOR:
    - Team-specific schedules → Use GetTeamGames instead
    - Betting lines → Use GetBettingLines for detailed spreads
    - Historical matchups → Use GetMatchupAnalysis
    
    Args:
        season: Year (defaults to current season based on date)
        week: Week 1-15 regular, 16+ postseason (defaults to current)
        team: Filter to specific team's games
        season_type: "regular" or "postseason"
        conference_game_only: Only conference matchups
    
    Examples:
        GetGames() → Current week's games by excitement
        GetGames(team="Alabama") → Alabama's games this season
        GetGames(week=10, conference_game_only=True) → Week 10 conference games
    """
```

### 4.5 Response Quality Improvements (Priority: HIGH)
**Goal**: Make responses more actionable and insightful.

#### Enhanced Summaries
```python
def generate_smart_summary(data, query_type):
    """Generate contextual summary based on query type"""
    
    if query_type == 'games':
        return {
            'marquee_matchup': find_best_game(data),
            'upset_alert': find_biggest_underdog_chance(data),
            'total_ranked_teams': count_ranked_teams(data),
            'average_spread': calculate_avg_spread(data),
            'viewing_recommendation': suggest_best_games(data, limit=3)
        }
    
    elif query_type == 'betting':
        return {
            'best_value': find_line_value(data),
            'public_vs_sharp': analyze_betting_splits(data),
            'trend': identify_betting_pattern(data),
            'confidence_plays': high_confidence_bets(data)
        }
```

#### Natural Language Insights
```python
def generate_insights(data):
    """Create human-readable insights"""
    insights = []
    
    # Pattern detection
    if detect_home_dominance(data):
        insights.append("Home teams are 8-2 ATS this week")
    
    if detect_scoring_trend(data):
        insights.append("Overs hitting at 65% in conference games")
        
    # Anomaly detection
    if unusual_line_movement(data):
        insights.append("Sharp money moving Ohio State line from -7 to -4")
        
    return insights
```

### 4.6 Error Messages and Recovery (Priority: MEDIUM)
**Goal**: Helpful error messages that guide users to success.

#### Smart Error Handling
```python
class UserFriendlyError:
    @staticmethod
    def handle_team_not_found(team_input):
        similar = find_similar_teams(team_input)
        return f"""
        Couldn't find team "{team_input}".
        
        Did you mean one of these?
        {format_suggestions(similar)}
        
        You can search teams with: SearchTeams("{team_input}")
        """
    
    @staticmethod  
    def handle_invalid_week(week, season):
        return f"""
        Week {week} not valid for {season} season.
        
        Regular season: Weeks 1-15
        Postseason starts: Week 16
        Current week: {get_current_week()}
        
        Try: GetGames(season={season}, week={get_current_week()})
        """
```

### 4.7 Quick Actions and Shortcuts (Priority: LOW)
**Goal**: Common queries should be one tool call.

#### Composite Shortcuts
```python
@mcp.tool()
async def GetTopGames(
    limit: Optional[Union[str, int]] = 10
) -> str:
    """Shortcut to get this week's best games.
    
    Equivalent to GetGames() with smart filtering for:
    - Ranked matchups
    - High excitement scores
    - Close spreads
    - Conference implications
    """
    
@mcp.tool()
async def GetUpsetWatch(
    week: Optional[Union[str, int]] = None
) -> str:
    """Get games with highest upset potential.
    
    Filters for:
    - Large underdogs with momentum
    - Historical upset spots
    - Matchup advantages for underdog
    """
```

## Implementation Guidelines

### Tool Selection Matrix
| User Query Pattern | Recommended Tool | Fallback Tool |
|-------------------|-----------------|---------------|
| "games this week" | GetGames | GetGamesByWeek |
| "Alabama schedule" | GetTeamGames | GetGames(team=) |
| "who will win X vs Y" | GetMatchupAnalysis | GetGames + GetAdvancedMetrics |
| "playoff chances" | GetPlayoffProjections | GetRankings |
| "best bets" | GetBettingAnalysis | GetBettingLines |
| "recruiting class" | GetRecruitingClass | GetRecruits |

### Parameter Standardization
```python
# All tools should accept these formats
team: "Alabama" | "BAMA" | "alabama" | 333 | "Crimson Tide"
season: 2024 | "2024" | None (auto-current)
week: 10 | "10" | "ten" | None (auto-current)
boolean: True | "true" | "yes" | 1 | "on"
```

### Response Consistency
```yaml
# All tools return this structure
summary:
  description: "Human-readable summary"
  total_results: 50
  key_insight: "Most important finding"
  
data:
  # Tool-specific data
  
metadata:
  generated_at: "2024-01-15T10:30:00Z"
  season: 2024
  week: 10
  confidence: 0.85
  
suggestions:
  - "Try GetMatchupAnalysis for deeper dive"
  - "Use GetBettingLines for spread details"
```

## Testing User Scenarios

### Scenario 1: Casual Fan
```
User: "what games should i watch this weekend"
Expected: GetGames() with excitement ordering
Response includes: Top 3-5 games with why they matter
```

### Scenario 2: Bettor
```
User: "give me the best bets for week 10"
Expected: GetBettingAnalysis(week=10)
Response includes: Value plays, line movement, trends
```

### Scenario 3: Team Fan
```
User: "how's Ohio State doing"
Expected: GetTeamGames(team="Ohio State") or GetTeamMomentum
Response includes: Recent results, ranking, upcoming games
```

### Scenario 4: Recruit Watcher
```
User: "who has the best recruiting class"
Expected: GetRecruitingClass(limit=10) ordered by ranking
Response includes: Top classes with star averages
```

## Success Metrics
- Tool selection accuracy > 90%
- Parameter inference success > 85%
- User satisfaction with first response > 80%
- Reduced clarification questions by 50%

## Implementation Priority
1. **Week 4, Day 3**: Smart parameter inference
2. **Week 4, Day 4**: Natural language team resolution  
3. **Week 4, Day 5**: Enhanced tool descriptions
4. **Week 5, Day 1**: Response quality improvements
5. **Week 5, Day 2**: Error handling and shortcuts

## Rollout Strategy
1. A/B test new inference logic
2. Collect user feedback on responses
3. Iterate on tool descriptions based on LLM performance
4. Monitor tool selection patterns
5. Refine based on real usage