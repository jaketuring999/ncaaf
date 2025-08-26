"""
Betting-related GraphQL queries for college football data.
"""

GET_BETTING_LINES_WITH_SEASON_WEEK_QUERY = """
query GetBettingLines($season: smallint!, $week: smallint!, $limit: Int) {
    game(
        where: {
            season: { _eq: $season }
            week: { _eq: $week }
            lines: {}
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: DESC }
        ]
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        excitement
        conferenceGame
        neutralSite
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

GET_BETTING_LINES_WITH_SEASON_QUERY = """
query GetBettingLines($season: smallint!, $limit: Int) {
    game(
        where: {
            season: { _eq: $season }
            lines: {}
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: DESC }
        ]
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        excitement
        conferenceGame
        neutralSite
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

GET_BETTING_LINES_WITH_WEEK_QUERY = """
query GetBettingLines($week: smallint!, $limit: Int) {
    game(
        where: {
            week: { _eq: $week }
            lines: {}
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: DESC }
        ]
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        excitement
        conferenceGame
        neutralSite
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

GET_BETTING_LINES_WITH_TEAM_QUERY = """
query GetBettingLines($teamId: Int!, $season: smallint, $limit: Int) {
    game(
        where: {
            _and: [
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
                { season: { _eq: $season } }
                { lines: {} }
            ]
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: DESC }
        ]
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        excitement
        conferenceGame
        neutralSite
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

GET_BETTING_LINES_WITH_TEAM_NO_SEASON_QUERY = """
query GetBettingLines($teamId: Int!, $limit: Int) {
    game(
        where: {
            _and: [
                {
                    _or: [
                        { homeTeamId: { _eq: $teamId } }
                        { awayTeamId: { _eq: $teamId } }
                    ]
                }
                { lines: {} }
            ]
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: DESC }
        ]
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        excitement
        conferenceGame
        neutralSite
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

GET_ALL_BETTING_LINES_QUERY = """
query GetBettingLines($limit: Int) {
    game(
        where: {
            lines: {}
        }
        orderBy: [
            { excitement: DESC_NULLS_LAST }
            { conferenceGame: DESC }
            { startDate: DESC }
        ]
        limit: $limit
    ) {
        id
        season
        week
        startDate
        status
        homeTeam
        awayTeam
        homePoints
        awayPoints
        excitement
        conferenceGame
        neutralSite
        
        # ELO Ratings
        awayStartElo
        homeStartElo
        awayEndElo
        homeEndElo
        
        # Win Probabilities
        awayPostgameWinProb
        homePostgameWinProb
        
        homeTeamInfo {
            teamId
            school
            conference
        }
        
        awayTeamInfo {
            teamId
            school
            conference
        }
        
        lines {
            spread
            spreadOpen
            overUnder
            overUnderOpen
            moneylineHome
            moneylineAway
        }
    }
}
"""

GET_TEAM_NAME_QUERY = """
query GetTeamName($teamId: Int!) {
    currentTeams(where: { teamId: { _eq: $teamId } }) {
        school
    }
}
"""