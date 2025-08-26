"""
Game-related GraphQL queries for college football data.
"""

GET_GAMES_WITH_SEASON_WEEK_SEASONTYPE_QUERY = """
query GetGames(
    $season: smallint!
    $week: smallint!
    $seasonType: season_type!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
            seasonType: { _eq: $seasonType }
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_GAMES_WITH_SEASON_WEEK_QUERY = """
query GetGames(
    $season: smallint!
    $week: smallint!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_GAMES_WITH_SEASON_SEASONTYPE_QUERY = """
query GetGames(
    $season: smallint!
    $seasonType: season_type!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            seasonType: { _eq: $seasonType }
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_GAMES_WITH_SEASON_QUERY = """
query GetGames(
    $season: smallint!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_GAMES_WITH_WEEK_QUERY = """
query GetGames(
    $week: smallint!
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        where: {
            week: { _eq: $week }
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_ALL_GAMES_QUERY = """
query GetGames(
    $includeBettingLines: Boolean = false
    $includeWeather: Boolean = false
    $includeMedia: Boolean = false
    $limit: Int
) {
    game(
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        venueId
        homePoints
        awayPoints
        notes
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        weather @include(if: $includeWeather) {
            condition {
                id
                description
            }
            temperature
            dewpoint
            humidity
            precipitation
            pressure
            snowfall
            windDirection
            windGust
            windSpeed
            weatherConditionCode
        }
        
        mediaInfo @include(if: $includeMedia) {
            mediaType
            name
        }
        
        lines @include(if: $includeBettingLines) {
            spread
            spreadOpen
            moneylineHome
            moneylineAway
            overUnder
            overUnderOpen
        }
    }
}
"""

GET_GAMES_BY_WEEK_QUERY = """
query GetGamesByWeek(
    $season: smallint!
    $week: smallint!
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        homePoints
        awayPoints
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""

GET_TEAM_GAMES_WITH_SEASON_QUERY = """
query GetTeamGames(
    $teamId: Int!
    $season: smallint!
    $limit: Int
) {
    game(
        where: {
            season: { _eq: $season }
            _or: [
                { homeTeamId: { _eq: $teamId } }
                { awayTeamId: { _eq: $teamId } }
            ]
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        homePoints
        awayPoints
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""

GET_TEAM_GAMES_QUERY = """
query GetTeamGames(
    $teamId: Int!
    $limit: Int
) {
    game(
        where: {
            _or: [
                { homeTeamId: { _eq: $teamId } }
                { awayTeamId: { _eq: $teamId } }
            ]
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { startDate: ASC }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        startTimeTbd
        status
        neutralSite
        attendance
        homePoints
        awayPoints
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""

GET_RECENT_GAMES_QUERY = """
query GetRecentGames($limit: Int) {
    game(
        where: {
            status: { _eq: "completed" }
        }
        orderBy: [
            { startDate: DESC }
            { excitement: DESC_NULLS_LAST }
        ]
        limit: $limit
    ) {
        id
        season
        seasonType
        week
        startDate
        status
        homePoints
        awayPoints
        excitement
        conferenceGame
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        # Line Scores (quarter by quarter)
        awayLineScores
        homeLineScores
        
        homeTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            abbreviation
            conference
        }
    }
}
"""