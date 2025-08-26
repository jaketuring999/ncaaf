# User Query Examples & Tool Mapping

## Common User Queries and How Improved Tools Handle Them

### 1. Game Information Queries

#### "What games are on this weekend?"
**Current Tool**: GetGames()
**Improvements Applied**:
- ✅ Auto-detects current week
- ✅ Sorts by excitement index
- ✅ Shows conference games first
- ✅ Includes venue and attendance

**Enhanced Response**:
```yaml
summary:
  marquee_game: "#3 Ohio State @ #2 Michigan (Excitement: 92.3)"
  total_games: 52
  ranked_matchups: 8
  average_spread: 13.5
  
must_watch:
  1: Ohio State @ Michigan - Big Ten East decider
  2: Alabama vs Auburn - Iron Bowl rivalry
  3: USC @ UCLA - Pac-12 implications
```

#### "Who's playing who in the SEC this week?"
**Tool**: GetGames(conference="SEC", week=current)
**New Features**:
- Conference filtering
- Rivalry game indicators
- Division standings impact

### 2. Betting/Prediction Queries

#### "Who's going to win Alabama vs Georgia?"
**New Tool**: GetMatchupAnalysis("Alabama", "Georgia")
**Provides**:
- Head-to-head history
- Current form comparison
- Advanced metrics matchup
- ELO-based prediction
- Key matchup advantages
- Weather impact

**Response Structure**:
```yaml
prediction:
  winner: "Georgia"
  confidence: 72%
  predicted_score: "Georgia 31, Alabama 24"
  
key_factors:
  - "Georgia defense allows 3.2 YPC (Alabama averages 5.1)"
  - "Alabama struggles vs elite pass rush (28% pressure rate)"
  - "Georgia 5-1 ATS as favorite vs ranked teams"
  
historical:
  h2h_last_5: "Georgia 3-2"
  avg_total_points: 48.5
```

#### "What are the best bets this week?"
**Enhanced Tool**: GetBettingAnalysis(week=current, analysis_type="value")
**New Capabilities**:
- Line value identification
- Sharp vs public money
- Trend analysis
- Situational spots

### 3. Team Performance Queries

#### "How's Ohio State doing lately?"
**New Tool**: GetTeamMomentum("Ohio State")
**Provides**:
- Last 5 games with context
- ELO rating trajectory
- Offensive/defensive trends
- Injury report impact
- Upcoming schedule difficulty

**Response**:
```yaml
momentum: "RISING"
recent_form: "4-1 last 5 (only loss to #1 Georgia)"
elo_change: "+45 points over 3 weeks"
key_trends:
  - "Averaging 42 PPG last 3 games"
  - "Defense allowing 14 PPG last 3"
  - "4-1 ATS as favorite"
red_flags:
  - "Starting RB questionable"
  - "0-2 in night games"
```

### 4. Recruiting Queries

#### "Who are the top recruits this year?"
**New Tool**: GetRecruits(min_stars=5, limit=20)
**Provides**:
- 5-star prospects ranked
- Position breakdown
- Commitment status
- Geographic distribution

#### "How's Alabama's recruiting class?"
**New Tool**: GetRecruitingClass("Alabama")
**Response**:
```yaml
class_summary:
  national_rank: 2
  conference_rank: 1
  total_commits: 23
  average_rating: 92.4
  five_stars: 3
  four_stars: 15
  
top_commits:
  1: "John Smith - QB - 5⭐ - #2 overall"
  2: "Mike Jones - DE - 5⭐ - #8 overall"
  
position_needs_filled:
  QB: ✅ (1 commit)
  RB: ✅ (2 commits)
  WR: ⚠️ (only 1 commit)
```

### 5. Transfer Portal Queries

#### "Who transferred from Oklahoma?"
**New Tool**: GetTransfers(from_team="Oklahoma")
**Shows**:
- Players who left
- Destination schools
- Positions impacted
- Ratings/experience

#### "What QBs are in the transfer portal?"
**New Tool**: GetTransfers(position="QB", uncommitted=True)
**Provides**:
- Available QBs ranked by rating
- Previous stats
- Eligibility remaining

### 6. Historical/Statistical Queries

#### "What's the Alabama vs Auburn all-time record?"
**Enhanced Tool**: GetMatchupAnalysis("Alabama", "Auburn", include_history=True)
**Includes**:
- All-time series record
- Venue records
- Largest victories
- Recent trends
- Notable games

### 7. Conference/Playoff Queries

#### "Who can still win the Big Ten?"
**New Tool**: GetConferenceRace("Big Ten")
**Provides**:
- Current standings
- Remaining schedules
- Tiebreaker scenarios
- Championship game projections

#### "What are Ohio State's playoff chances?"
**New Tool**: GetPlayoffProjections(team="Ohio State")
**Response**:
```yaml
playoff_probability: 68%
current_ranking: 5
path_to_playoff:
  - "Must win out (3 games remaining)"
  - "Need 1 loss from Georgia or Michigan"
  - "Win Big Ten Championship"
scenarios:
  best_case: "Win out + chaos = 95% chance"
  worst_case: "Loss to Michigan = 5% chance"
```

### 8. Advanced Analytics Queries

#### "Which teams are better than their record?"
**New Tool**: GetSeasonTrends(trend_type="underperforming")
**Identifies**:
- Teams with positive EPA but losing record
- Unlucky turnover margins
- Close game records
- Strength of schedule impact

#### "Show me upset alerts for this week"
**New Tool**: GetUpsetWatch()
**Analyzes**:
- Large underdogs with advantages
- Matchup-specific edges
- Historical upset spots
- Line movement indicators

### 9. Multi-Part Queries

#### "I want to bet on SEC games this week, what should I know?"
**Tools Used**:
1. GetGames(conference="SEC") - Get the games
2. GetBettingLines(conference="SEC") - Get the lines
3. GetBettingAnalysis(conference="SEC") - Get insights

**Unified Response**:
```yaml
sec_betting_guide:
  total_games: 7
  
  best_bets:
    1: "Georgia -7 (should be -10)"
    2: "Tennessee/Kentucky Over 58.5"
    
  trends:
    - "SEC home teams 18-5 ATS"
    - "Unders hitting 62% in conference"
    
  trap_games:
    - "Avoid: Arkansas +21 (lookahead spot)"
```

### 10. Natural Language Variations

#### Different Ways to Ask Same Question
All map to GetTeamGames("Alabama"):
- "Alabama schedule"
- "When does Bama play?"
- "Show me the Crimson Tide games"
- "Who has Alabama played?"
- "alabama football games"
- "BAMA games"

#### Team Name Resolution Examples
All resolve to "Ohio State":
- "OSU" (with context)
- "tOSU"
- "Buckeyes"
- "Ohio St"
- "Ohio State University"
- "Columbus" (with football context)

## Error Handling Examples

### Query: "Show me games for the Tiggers"
**Response**:
```
Couldn't find team "Tiggers".

Did you mean one of these?
• Tigers (LSU)
• Tigers (Auburn) 
• Tigers (Clemson)
• Tigers (Missouri)

Try: GetTeamGames("LSU") for LSU Tigers
```

### Query: "Games for week 25"
**Response**:
```
Week 25 is not valid for the 2024 season.

Regular season: Weeks 1-15
Bowl season: Weeks 16-19
Current week: Week 10

Showing Week 10 games instead...
```

## Tool Selection Logic

### Decision Tree for Common Queries

```
User asks about games
├── Specific team mentioned?
│   └── Yes → GetTeamGames
│   └── No → Continue
├── Betting/spread mentioned?
│   └── Yes → GetBettingLines or GetBettingAnalysis
│   └── No → Continue  
├── Two teams mentioned?
│   └── Yes → GetMatchupAnalysis
│   └── No → Continue
├── Week/date mentioned?
│   └── Yes → GetGamesByWeek
│   └── No → GetGames (current week)
```

## Performance Improvements

### Before Improvements
```
User: "Good games this week?"
Tool: GetGames()
Response: 50 games ordered by date
User: "Which ones are close?"
Tool: GetGames() again
Response: Filter manually
User: "Any ranked teams?"
Tool: Need another query...
```

### After Improvements
```
User: "Good games this week?"
Tool: GetGames() with excitement ordering
Response: Top 5 games with:
  - Excitement scores
  - Ranked team indicators
  - Spread (close game indicator)
  - Why each matters
  
All info in one query!
```

## Success Metrics Tracking

### Query Resolution Rate
- **Before**: 60% answered in one tool call
- **Target**: 85% answered in one tool call
- **Measurement**: Track follow-up questions

### Tool Selection Accuracy
- **Before**: 70% correct tool first try
- **Target**: 90% correct tool first try
- **Measurement**: Track tool switching

### User Satisfaction
- **Before**: Users need 2-3 queries average
- **Target**: 1.5 queries average
- **Measurement**: Session query count