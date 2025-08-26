# Phase 1: Core Query Enhancements

## Overview
Enhance existing queries to better utilize available GraphQL fields and provide smarter ordering. This phase focuses on making current tools more powerful without changing their interfaces.

## Tasks

### 1.1 Enhance Game Queries (Priority: HIGH)
**Files**: `queries/games.py`, `tools/games.py`

#### Enhancements

##### A. Add Predictive Fields to BASE_GAME_FIELDS
```python
# Add to game queries
awayStartElo
homeStartElo  
awayEndElo
homeEndElo
awayPostgameWinProb
homePostgameWinProb
```

##### B. Add Line Score Data
```python
# Quarter/period scoring for game flow analysis
awayLineScores
homeLineScores
```

##### C. Add Venue Context
```python
venueId
attendance
neutralSite
```

#### Implementation
```python
# queries/games.py - Update BASE_GAME_FIELDS
BASE_GAME_FIELDS = """
    id
    season
    week
    startDate
    completed
    excitement
    conferenceGame
    neutralSite
    attendance
    venueId
    awayId
    awayTeam
    awayConference
    awayPoints
    awayStartElo
    awayEndElo
    awayPostgameWinProb
    awayLineScores
    homeId
    homeTeam
    homeConference
    homePoints
    homeStartElo
    homeEndElo
    homePostgameWinProb
    homeLineScores
"""
```

### 1.2 Enhance Betting Queries (Priority: HIGH)
**Files**: `queries/betting.py`

#### Current Issues
- Simple date-based ordering misses exciting games
- No correlation with game importance

#### Enhancements

##### A. Update Ordering Strategy
```python
# queries/betting.py - All betting queries
# Change from:
orderBy: { startDate: DESC }
# To:
orderBy: [
    { excitement: DESC_NULLS_LAST }
    { conferenceGame: DESC }
    { startDate: DESC }
]
```

##### B. Add Win Probability to Betting Context
```python
# Include in BETTING_LINES_QUERY
game {
    awayPostgameWinProb
    homePostgameWinProb
    excitement
}
```

### 1.3 Enhance Team Metrics Queries (Priority: MEDIUM)
**Files**: `queries/metrics.py`

#### Current Issues
- Only querying 5 basic fields from rich AdjustedTeamMetrics
- Missing defensive metrics
- No special teams data

#### Enhancements

##### A. Expand Offensive Metrics
```python
# Add to ADVANCED_METRICS_QUERY
offensiveRushingEpa
offensivePassingEpa
rushingSuccessRate
passingSuccessRate
explosiveness
lineYards
secondLevelYards
openFieldYards
passingDownSuccessRate
standardDownsSuccessRate
```

##### B. Add Defensive Metrics
```python
# All "Allowed" fields
defensiveRushingEpaAllowed
defensivePassingEpaAllowed
rushingSuccessRateAllowed
passingSuccessRateAllowed
explosivenessAllowed
lineYardsAllowed
havoc
```

##### C. Add Special Teams
```python
specialTeamsEpa
fieldGoalEpa
puntEpa
kickoffEpa
```

### 1.4 Enhance Rankings with Movement (Priority: MEDIUM)
**Files**: `queries/rankings.py`, `utils/response_formatter.py`

#### Current Issues
- No week-over-week movement tracking
- Missing voting points data

#### Enhancements

##### A. Add Points Field
```python
# queries/rankings.py
points  # Voting points received
firstPlaceVotes
```

##### B. Calculate Movement in Formatter
```python
# utils/response_formatter.py
def calculate_ranking_movement(current_week, previous_week):
    """Calculate ranking changes between weeks"""
    # Implementation to show ↑5, ↓2, NEW, etc.
```

### 1.5 Add Ratings to Team Queries (Priority: LOW)
**Files**: `queries/teams.py`

#### Current Issues
- No team strength ratings in responses
- Users need separate queries for ratings

#### Enhancements

##### A. Include Ratings in Team Details
```python
# Add relationship query
ratings(where: { season: { _eq: $season }}) {
    season
    teamId
    elo
    fpi {
        overall
        offense
        defense
    }
    sp {
        overall
        offense
        defense
        specialTeams
    }
    srs
}
```

## Testing Checklist


### Integration Tests
- [ ] Test each enhanced tool with real queries
- [ ] Verify response formatting
- [ ] Check performance impact


## Rollback Plan
1. Keep original queries in `queries/legacy/` folder
2. Feature flag for new vs old queries
3. Quick revert via configuration

## Success Criteria
- ✅ All existing tools continue to work
- ✅ New fields provide additional value
- ✅ Queries return in < 2 seconds
- ✅ Smarter ordering reduces follow-up queries by 30%

## Dependencies
- GraphQL schema remains stable
- No breaking changes to tool interfaces
- Existing tests pass with enhancements

Rating Systems (ratings type):
Contains multiple ranking fields:
fpiAvgWinProbabilityRank
fpiGameControlRank
fpiRemainingSosRank
fpiResumeRank
fpiSosRank
fpiStrengthOfRecordRank
