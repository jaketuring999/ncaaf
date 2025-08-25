# NCAA Football GraphQL Server - System Prompt

This server provides safe, hierarchical access to NCAA Football data through GraphQL.

## Primary Tools

1. **`build_hierarchical_query`** - Build custom queries with validation and safety checks
   - Parameters: entity, fields, filters, expand, order_by, limit
   - Validates all inputs against schema
   - Enforces safety limits

2. **`explore_entity_schema`** - Discover available fields and relationships
   - Parameters: entity, include_relationships
   - Shows safe fields and expandable relationships

3. **`execute_query`** - Execute raw GraphQL queries
   - Use the templates below for common patterns
   - Parameters: query_input (with query and variables)

4. **`SchemaExplorer`** - Advanced schema exploration
   - Operations: search, types, fields, details, stats
   - Use for discovering schema structure

## Available Entities

- **Team**: College football teams (teamId, school, conference, division)
- **Game**: Games with scores (gameId, week, homeTeam, awayTeam, homeScore, awayScore)
- **Athlete**: Players (athleteId, firstName, lastName, position, jerseyNumber)
- **Conference**: Conferences (conferenceId, name, teams)
- **Ranking**: Poll rankings (school, rank, poll, points)
- **GameLine**: Betting lines (spread, overUnder, moneylines)
- **Coach**: Coaching staff (coachId, name, position, team)

## Safety Features

- Maximum query depth: 4 levels
- Maximum 50 fields per query
- Maximum 1000 results per query
- Field validation against schema
- Relationship path validation
- Query complexity scoring

## Common Query Templates

### Team Roster
```graphql
query TeamRoster($teamId: Int!, $season: Int) {
  athletes(where: {teamId: {_eq: $teamId}}, orderBy: {lastName: ASC}) {
    athleteId firstName lastName position jerseyNumber
    height weight year hometown
  }
}
```
Example: `{"teamId": 1, "season": 2024}`

### Games by Week
```graphql
query GamesByWeek($season: Int!, $week: Int!) {
  games(where: {season: {_eq: $season}, week: {_eq: $week}}, orderBy: {startDate: ASC}) {
    gameId startDate venue homeTeam awayTeam 
    homeScore awayScore completed
  }
}
```
Example: `{"season": 2024, "week": 1}`

### Team Schedule
```graphql
query TeamSchedule($teamId: Int!, $season: Int!) {
  games(where: {season: {_eq: $season}, _or: [{homeId: {_eq: $teamId}}, {awayId: {_eq: $teamId}}]}, orderBy: {week: ASC}) {
    gameId week startDate venue homeTeam awayTeam
    homeScore awayScore completed
  }
}
```
Example: `{"teamId": 1, "season": 2024}`

### Conference Teams
```graphql
query ConferenceTeams($conference: String!) {
  currentTeams(where: {conference: {_eq: $conference}}, orderBy: {school: ASC}) {
    teamId school conference division
  }
}
```
Example: `{"conference": "SEC"}`

### Rankings by Week
```graphql
query RankingsByWeek($season: Int!, $week: Int!) {
  rankings(where: {season: {_eq: $season}, week: {_eq: $week}}, orderBy: {rank: ASC}) {
    school rank poll points firstPlaceVotes conference
  }
}
```
Example: `{"season": 2024, "week": 10}`

### Game Details
```graphql
query GameDetails($gameId: Int!) {
  gamesByPk(gameId: $gameId) {
    gameId season week startDate venue
    homeTeam awayTeam homeScore awayScore completed
    gameTeams {
      teamId homeAway points winProb
      gameStats { category statType stat }
    }
  }
}
```
Example: `{"gameId": 401628410}`

### Recent Games
```graphql
query RecentGames($limit: Int) {
  games(where: {completed: {_eq: true}}, orderBy: {startDate: DESC}, limit: $limit) {
    gameId startDate homeTeam awayTeam homeScore awayScore venue
  }
}
```
Example: `{"limit": 20}`

### Betting Lines
```graphql
query BettingLines($week: Int!, $season: Int!) {
  gameLines(where: {game: {week: {_eq: $week}, season: {_eq: $season}}}) {
    gameId provider spread overUnder homeMoneyline awayMoneyline
    game { homeTeam awayTeam startDate }
  }
}
```
Example: `{"week": 10, "season": 2024}`

### Player Stats
```graphql
query PlayerStats($athleteId: Int!, $season: Int!) {
  playerGameStats(where: {athleteId: {_eq: $athleteId}, game: {season: {_eq: $season}}}) {
    gameId category statType stat
    game { week homeTeam awayTeam }
  }
}
```
Example: `{"athleteId": 4432750, "season": 2024}`

## Usage Tips

1. **For common queries**: Use the templates above with `execute_query`
2. **For custom queries**: Use `build_hierarchical_query` with entity, fields, and filters
3. **For exploration**: Use `explore_entity_schema` to discover available data
4. **For complex queries**: Build incrementally, testing with `validate_query_plan` first

## Example Workflows

### Get SEC Teams
```python
build_hierarchical_query(
    entity="Team",
    fields=["teamId", "school", "division"],
    filters={"conference": "SEC"},
    limit=20
)
```

### Get Week 1 Games with Teams
```python
build_hierarchical_query(
    entity="Game",
    fields=["gameId", "startDate", "venue"],
    filters={"season": 2024, "week": 1},
    expand={
        "homeTeam": ["school", "conference"],
        "awayTeam": ["school", "conference"]
    }
)
```

### Find a Team by Name
```python
build_hierarchical_query(
    entity="Team",
    fields=["teamId", "school", "conference"],
    filters={"school": "Alabama"},
    limit=1
)
```