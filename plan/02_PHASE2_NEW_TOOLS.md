# Phase 2: New Tools for Missing Capabilities

## Overview
Create new MCP tools to expose important GraphQL schema capabilities that aren't currently accessible. Focus on high-value data that users frequently ask about.

## New Tools Implementation

### 2.1 Recruiting Tools (Priority: CRITICAL)
**Why**: Recruiting is fundamental to college football. Users frequently ask about commitments, class rankings, and top prospects.

#### Tool: GetRecruits
```python
# tools/recruiting.py
@mcp.tool()
async def GetRecruits(
    team: Optional[str] = None,
    season: Optional[Union[str, int]] = None,
    position: Optional[str] = None,
    state: Optional[str] = None,
    min_stars: Optional[Union[str, int]] = None,
    committed_only: Optional[Union[str, bool]] = False,
    limit: Optional[Union[str, int]] = 50
) -> str:
    """Get recruiting information with flexible filtering.
    
    Users often ask:
    - "Who has Ohio State recruited?"
    - "Show me 5-star quarterbacks"
    - "What's Alabama's recruiting class?"
    - "Top recruits from Texas"
    """
```

#### Tool: GetRecruitingClass
```python
@mcp.tool()
async def GetRecruitingClass(
    team: str,
    season: Optional[Union[str, int]] = None,
    include_rankings: Optional[Union[str, bool]] = True
) -> str:
    """Get complete recruiting class for a team.
    
    Returns:
    - Overall class ranking
    - Average star rating
    - List of commits with positions
    - Comparison to conference rivals
    """
```

#### GraphQL Query
```graphql
query GetRecruits($teamId: Int, $season: Int, $minRating: Float) {
  recruit(
    where: {
      season: { _eq: $season }
      stars: { _gte: $minStars }
      recruitSchools: { teamId: { _eq: $teamId }}
    }
    orderBy: [
      { stars: DESC }
      { rating: DESC }
    ]
  ) {
    id
    season
    name
    position
    height
    weight
    stars
    rating
    city
    stateProvince
    committedTo
    recruitSchools {
      school
      committedTo
    }
  }
}
```

### 2.2 Transfer Portal Tools (Priority: HIGH)
**Why**: Transfer portal has revolutionized college football. Users want to track player movement.

#### Tool: GetTransfers
```python
@mcp.tool()
async def GetTransfers(
    from_team: Optional[str] = None,
    to_team: Optional[str] = None,
    season: Optional[Union[str, int]] = None,
    position: Optional[str] = None,
    limit: Optional[Union[str, int]] = 50
) -> str:
    """Get transfer portal activity.
    
    Users often ask:
    - "Who transferred from Alabama?"
    - "What transfers did Georgia get?"
    - "Show me quarterback transfers"
    """
```

#### GraphQL Query
```graphql
query GetTransfers($fromTeam: String, $toTeam: String, $season: Int) {
  transfer(
    where: {
      season: { _eq: $season }
      fromTeam: { _eq: $fromTeam }
      toTeam: { _eq: $toTeam }
    }
    orderBy: { rating: DESC }
  ) {
    id
    season
    firstName
    lastName
    position
    fromTeam
    toTeam
    rating
    stars
    eligibility
  }
}
```

### 2.3 Coach Information Tools (Priority: MEDIUM)
**Why**: Coaching changes and history are major storylines. Users ask about coach records and career paths.

#### Tool: GetCoaches
```python
@mcp.tool()
async def GetCoaches(
    team: Optional[str] = None,
    season: Optional[Union[str, int]] = None,
    min_wins: Optional[Union[str, int]] = None
) -> str:
    """Get coach information and records.
    
    Users often ask:
    - "Who coaches Michigan?"
    - "What's Saban's record?"
    - "Show me new head coaches"
    """
```

#### Tool: GetCoachHistory
```python
@mcp.tool()
async def GetCoachHistory(
    coach_name: str
) -> str:
    """Get complete coaching history for a coach.
    
    Returns career progression, records at each stop, championships
    """
```

#### GraphQL Query
```graphql
query GetCoaches($team: String, $season: Int) {
  coach(
    where: {
      coachSeasons: {
        team: { _eq: $team }
        season: { _eq: $season }
      }
    }
  ) {
    id
    firstName
    lastName
    coachSeasons(orderBy: { season: DESC }) {
      season
      team
      games
      wins
      losses
      postseasonWins
      postseasonLosses
    }
  }
}
```

### 2.4 Draft Analytics Tools (Priority: LOW)
**Why**: NFL draft success is a measure of program strength. Users want to know about draft prospects.

#### Tool: GetDraftPicks
```python
@mcp.tool()
async def GetDraftPicks(
    team: Optional[str] = None,
    season: Optional[Union[str, int]] = None,
    round: Optional[Union[str, int]] = None,
    position: Optional[str] = None,
    limit: Optional[Union[str, int]] = 50
) -> str:
    """Get NFL draft picks from college teams.
    
    Users often ask:
    - "How many Alabama players were drafted?"
    - "First round picks from Ohio State"
    - "Which school had most draft picks?"
    """
```

### 2.5 Team Talent/Composite Tools (Priority: MEDIUM)
**Why**: Overall team talent is predictive of success. 247Sports composite rankings are widely referenced.

#### Tool: GetTeamTalent
```python
@mcp.tool()
async def GetTeamTalent(
    team: Optional[str] = None,
    season: Optional[Union[str, int]] = None,
    conference: Optional[str] = None,
    limit: Optional[Union[str, int]] = 25
) -> str:
    """Get team talent composite rankings.
    
    Shows overall roster talent based on recruiting rankings.
    Useful for understanding program strength beyond W-L record.
    """
```

#### GraphQL Query
```graphql
query GetTeamTalent($season: Int) {
  teamTalent(
    where: { season: { _eq: $season }}
    orderBy: { talent: DESC }
  ) {
    season
    teamId
    team
    conference
    talent  # Composite score
    rank
  }
}
```

### 2.6 Predicted Points (PPA) Tools (Priority: HIGH)
**Why**: PPA is advanced analytics for play calling and situational football.

#### Tool: GetPredictedPoints
```python
@mcp.tool()
async def GetPredictedPoints(
    down: Union[str, int],
    distance: Union[str, int],
    yard_line: Union[str, int],
    team: Optional[str] = None
) -> str:
    """Get predicted points for game situations.
    
    Users often ask:
    - "Should they go for it on 4th and 2?"
    - "Expected points from the 30 yard line"
    - "When to go for 2-point conversion"
    """
```

### 2.7 Game Player Stats Tools (Priority: MEDIUM)
**Why**: Individual player performance in specific games.

#### Tool: GetGamePlayerStats
```python
@mcp.tool()
async def GetGamePlayerStats(
    game_id: Optional[Union[str, int]] = None,
    player_name: Optional[str] = None,
    team: Optional[str] = None,
    stat_category: Optional[str] = None  # passing, rushing, receiving, defense
) -> str:
    """Get player statistics from specific games.
    
    Users often ask:
    - "How did Quinn Ewers perform?"
    - "Top rushers in the Alabama game"
    - "Defensive stats for Will Anderson"
    """
```

## Implementation Strategy

### Directory Structure
```
tools/
  recruiting.py     # New file
  transfers.py      # New file
  coaches.py        # New file
  draft.py          # New file
  talent.py         # New file
  ppa.py           # New file
  player_stats.py   # New file
  
queries/
  recruiting.py     # New file
  transfers.py      # New file
  coaches.py        # New file
  draft.py          # New file
  talent.py         # New file
  ppa.py           # New file
  player_stats.py   # New file
```

### Common Patterns
1. **Team Resolution**: All tools should accept team name, abbreviation, or ID
2. **Smart Defaults**: Current season, reasonable limits
3. **Flexible Parameters**: String or int for numeric values, string or bool for booleans
4. **Rich Responses**: Include context and related data

### Response Format Example
```yaml
summary:
  total_recruits: 25
  average_rating: 92.3
  average_stars: 3.8
  class_rank: 5
  conference_rank: 2
  
top_recruits:
  - name: "John Smith"
    position: "QB"
    stars: 5
    rating: 98.5
    hometown: "Dallas, TX"
    status: "Committed"
    
position_breakdown:
  QB: 2
  RB: 3
  WR: 5
  OL: 6
  # etc
```

## Testing Requirements

### Functional Tests
- [ ] Each tool returns valid responses
- [ ] Parameter validation works
- [ ] Error handling for invalid inputs

### Integration Tests
- [ ] Tools work with MCP framework
- [ ] Response formatting is consistent
- [ ] Performance under load

### User Acceptance
- [ ] Natural language maps to correct tools
- [ ] Responses answer user questions
- [ ] Data is accurate and current

## Success Metrics
- Coverage of all major recruiting questions
- Reduced need for custom GraphQL queries
- Transfer portal tracking capability
- Coach career visibility
- Draft success analytics

## Risks and Mitigations
- **Risk**: Schema changes break tools
  - **Mitigation**: Version queries, test regularly
  
- **Risk**: Too many tools confuse LLM
  - **Mitigation**: Clear descriptions, good examples
  
- **Risk**: Performance with large datasets
  - **Mitigation**: Smart limits, pagination

## Timeline
- Week 2, Day 1-2: Implement recruiting tools
- Week 2, Day 3: Transfer portal tools
- Week 2, Day 4: Coach information tools
- Week 2, Day 5: Team talent tool
- Week 3, Day 1-2: PPA and player stats tools
- Week 3, Day 3: Integration testing
- Week 3, Day 4-5: Documentation and examples