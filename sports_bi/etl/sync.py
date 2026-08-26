import json
from datetime import datetime
from typing import Any

from sqlalchemy import select

from sports_bi.app.database import SessionLocal, create_tables
from sports_bi.app.models import Competition, Coverage, Fixture, FixtureEvent, FixtureStatistic, Player, RawIngestion, Season, Standing, Team
from sports_bi.services.football_api import FootballAPI


def _raw(session: Any, endpoint: str, params: dict[str, Any], payload: list[dict[str, Any]]) -> None:
    session.add(RawIngestion(endpoint=endpoint, request_params=json.dumps(params, sort_keys=True), payload=json.dumps(payload), status_code=200))


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def sync_brazilian_competitions(api: FootballAPI | None = None) -> int:
    """Discover Brazilian competitions and preserve every received payload."""
    create_tables()
    football_api = api or FootballAPI()
    rows = football_api.competitions()
    with SessionLocal.begin() as session:
        _raw(session, "/leagues", {"country": "Brazil"}, rows)
        for item in rows:
            league = item.get("league", {})
            if not league.get("id"):
                continue
            competition = session.get(Competition, league["id"])
            if competition is None:
                competition = Competition(id=league["id"], name=league.get("name", "Unknown"))
                session.add(competition)
            competition.name = league.get("name", competition.name)
            country = item.get("country", {})
            competition.country = country.get("name") if isinstance(country, dict) else country
            competition.logo = league.get("logo")
            competition.type = league.get("type")
    return len(rows)


def sync_league_season(league_id: int, season_year: int, api: FootballAPI | None = None) -> dict[str, int]:
    """Load teams and fixtures for one league-season; unavailable data stays absent/NULL."""
    create_tables()
    football_api = api or FootballAPI()
    seasons = football_api.seasons(league_id)
    season_data = next((item for item in seasons if item.get("year") == season_year), None)
    teams = football_api.teams(league_id, season_year) if season_data else []
    fixtures = football_api.fixtures(league_id, season_year) if season_data else []
    with SessionLocal.begin() as session:
        _raw(session, "/leagues", {"id": league_id}, seasons)
        competition = session.get(Competition, league_id)
        if competition is None:
            raise ValueError(f"Competição {league_id} não está cadastrada")
        season = session.scalar(select(Season).where(Season.competition_id == league_id, Season.year == season_year))
        if season is None:
            season = Season(competition_id=league_id, year=season_year)
            session.add(season)
            session.flush()
        if season_data:
            season.start_date = season_data.get("start")
            season.end_date = season_data.get("end")
            season.current = bool(season_data.get("current", False))
        _raw(session, "/teams", {"league": league_id, "season": season_year}, teams)
        for item in teams:
            team_data = item.get("team", {})
            if not team_data.get("id"):
                continue
            team = session.get(Team, team_data["id"])
            if team is None:
                team = Team(id=team_data["id"], name=team_data.get("name", "Unknown"))
                session.add(team)
            team.name = team_data.get("name", team.name)
            team.code = team_data.get("code")
            team.country = team_data.get("country")
            team.logo = team_data.get("logo")
        _raw(session, "/fixtures", {"league": league_id, "season": season_year}, fixtures)
        for item in fixtures:
            fixture_data = item.get("fixture", {})
            teams_data = item.get("teams", {})
            goals = item.get("goals", {})
            if not fixture_data.get("id"):
                continue
            fixture = session.get(Fixture, fixture_data["id"])
            if fixture is None:
                fixture = Fixture(id=fixture_data["id"])
                session.add(fixture)
            fixture.competition_id = league_id
            fixture.season_id = season.id
            fixture.home_team_id = (teams_data.get("home") or {}).get("id")
            fixture.away_team_id = (teams_data.get("away") or {}).get("id")
            fixture.date = _date(fixture_data.get("date"))
            fixture.status = (fixture_data.get("status") or {}).get("short")
            fixture.round = (item.get("league") or {}).get("round")
            fixture.home_goals = goals.get("home")
            fixture.away_goals = goals.get("away")
    return {"season": int(bool(season_data)), "teams": len(teams), "fixtures": len(fixtures)}


def sync_fixture_details(fixture_id: int, api: FootballAPI | None = None) -> dict[str, int]:
    """Load optional events and statistics without inventing unsupported metrics."""
    create_tables()
    football_api = api or FootballAPI()
    events = football_api.events(fixture_id)
    statistics = football_api.statistics(fixture_id)
    with SessionLocal.begin() as session:
        _raw(session, "/fixtures/events", {"fixture": fixture_id}, events)
        for item in events:
            time_data = item.get("time") or {}
            team_data = item.get("team") or {}
            player_data = item.get("player") or {}
            player = None
            if player_data.get("id"):
                player = session.get(Player, player_data["id"])
                if player is None:
                    player = Player(id=player_data["id"], name=player_data.get("name", "Unknown"))
                    session.add(player)
            existing = session.query(FixtureEvent).filter_by(fixture_id=fixture_id, time_minute=time_data.get("elapsed"), team_id=team_data.get("id"), player_id=player_data.get("id"), type=item.get("type"), detail=item.get("detail")).first()
            if existing is None:
                session.add(FixtureEvent(fixture_id=fixture_id, team_id=team_data.get("id"), player_id=player_data.get("id"), time_minute=time_data.get("elapsed"), type=item.get("type"), detail=item.get("detail")))
        _raw(session, "/fixtures/statistics", {"fixture": fixture_id}, statistics)
        for team_block in statistics:
            team_id = (team_block.get("team") or {}).get("id")
            for metric in team_block.get("statistics") or []:
                name = metric.get("type")
                if name is None or team_id is None:
                    continue
                existing = session.query(FixtureStatistic).filter_by(fixture_id=fixture_id, team_id=team_id, metric=name).first()
                if existing is None:
                    session.add(FixtureStatistic(fixture_id=fixture_id, team_id=team_id, metric=name, value=str(metric.get("value")) if metric.get("value") is not None else None))
    return {"events": len(events), "statistics": len(statistics)}


def sync_standings(league_id: int, season_year: int, api: FootballAPI | None = None) -> int:
    """Load the standings endpoint when the provider exposes it for the slice."""
    create_tables()
    football_api = api or FootballAPI()
    rows = football_api.standings(league_id, season_year)
    with SessionLocal.begin() as session:
        season = session.scalar(select(Season).where(Season.competition_id == league_id, Season.year == season_year))
        if season is None:
            raise ValueError(f"Temporada {season_year} não está cadastrada para {league_id}")
        _raw(session, "/standings", {"league": league_id, "season": season_year}, rows)
        groups = (rows[0].get("league", {}).get("standings", []) if rows else [])
        entries = [entry for group in groups for entry in group]
        coverage = session.scalar(select(Coverage).where(Coverage.competition_id == league_id, Coverage.season_id == season.id, Coverage.endpoint == "/standings"))
        if coverage is None:
            coverage = Coverage(competition_id=league_id, season_id=season.id, endpoint="/standings")
            session.add(coverage)
        coverage.available = bool(entries)
        coverage.notes = None if entries else "Endpoint sem dados para esta competição e temporada"
        for entry in entries:
            team_id = (entry.get("team") or {}).get("id")
            if team_id is None:
                continue
            standing = session.scalar(select(Standing).where(Standing.competition_id == league_id, Standing.season_id == season.id, Standing.team_id == team_id))
            if standing is None:
                standing = Standing(competition_id=league_id, season_id=season.id, team_id=team_id)
                session.add(standing)
            standing.position = entry.get("rank")
            standing.played = (entry.get("all") or {}).get("played")
            standing.wins = (entry.get("all") or {}).get("win")
            standing.draws = (entry.get("all") or {}).get("draw")
            standing.losses = (entry.get("all") or {}).get("lose")
            standing.goals_for = (entry.get("all", {}).get("goals") or {}).get("for")
            standing.goals_against = (entry.get("all", {}).get("goals") or {}).get("against")
            standing.points = entry.get("points")
    return len(entries)


if __name__ == "__main__":
    print(f"Competições sincronizadas: {sync_brazilian_competitions()}")
