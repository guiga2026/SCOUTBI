import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from sports_bi.app.database import Base
from sports_bi.app.models import Competition, Fixture, RawIngestion, Season, Team
from sports_bi.quality import build_quality_report


def test_quality_report_measures_loaded_fixtures_and_teams() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Competition(id=72, name="Serie B"))
        session.add(Season(id=1, competition_id=72, year=2024))
        session.add(Team(id=10, name="Home"))
        session.add(Team(id=11, name="Away"))
        session.add(Fixture(id=100, competition_id=72, season_id=1, home_team_id=10, away_team_id=11))
        session.add(RawIngestion(endpoint="/teams", request_params=json.dumps({"league": 72, "season": 2024}), payload=json.dumps([{"team": {"id": 10}}, {"team": {"id": 11}}]), status_code=200))
        session.add(RawIngestion(endpoint="/fixtures", request_params=json.dumps({"league": 72, "season": 2024}), payload=json.dumps([{"fixture": {"id": 100}}]), status_code=200))
        session.commit()
        report = build_quality_report(session, 72, 2024)
    assert report["fixtures"]["found"] == 1
    assert report["fixtures"]["coverage_percent"] == 100.0
    assert report["teams"]["found"] == 2
    assert report["players"]["status"] == "unavailable"
