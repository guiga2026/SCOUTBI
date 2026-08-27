import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sports_bi.app.models import Fixture, RawIngestion, Season, Team


def _payload_rows(session: Session, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for ingestion in session.scalars(select(RawIngestion).where(RawIngestion.endpoint == endpoint)).all():
        try:
            stored_params = json.loads(ingestion.request_params)
            if all(stored_params.get(key) == value for key, value in params.items()):
                payload = json.loads(ingestion.payload)
                if isinstance(payload, list):
                    result.extend(payload)
        except (TypeError, ValueError):
            continue
    return result


def _percentage(found: int, expected: int | None) -> float | None:
    return round(found * 100 / expected, 2) if expected else None


def build_quality_report(session: Session, competition_id: int, season_year: int) -> dict[str, Any]:
    season = session.scalar(select(Season).where(Season.competition_id == competition_id, Season.year == season_year))
    if season is None:
        return {"competition_id": competition_id, "season_year": season_year, "status": "not_loaded", "reason": "Season not found"}
    fixture_source = _payload_rows(session, "/fixtures", {"league": competition_id, "season": season_year})
    team_source = _payload_rows(session, "/teams", {"league": competition_id, "season": season_year})
    fixture_count = session.scalar(select(func.count(Fixture.id)).where(Fixture.competition_id == competition_id, Fixture.season_id == season.id)) or 0
    team_ids = {item.get("team", {}).get("id") for item in team_source if isinstance(item.get("team"), dict) and item.get("team", {}).get("id") is not None}
    loaded_team_count = session.scalar(select(func.count(Team.id)).where(Team.id.in_(team_ids))) if team_ids else 0
    duplicate_fixture_ids = len(fixture_source) - len({(item.get("fixture") or {}).get("id") for item in fixture_source})
    latest_sync = session.scalar(select(func.max(RawIngestion.collected_at)).where(RawIngestion.endpoint.in_(("/fixtures", "/teams"))))
    age_hours = round((datetime.now(timezone.utc).replace(tzinfo=None) - latest_sync).total_seconds() / 3600, 2) if latest_sync else None
    return {
        "competition_id": competition_id,
        "season_id": season.id,
        "season_year": season_year,
        "status": "available",
        "fixtures": {"expected": len(fixture_source) or None, "found": fixture_count, "coverage_percent": _percentage(fixture_count, len(fixture_source))},
        "teams": {"expected": len(team_ids) or None, "found": loaded_team_count, "coverage_percent": _percentage(loaded_team_count, len(team_ids))},
        "players": {"found": None, "with_statistics": None, "coverage_percent": None, "status": "unavailable", "reason": "Player lineup/statistics ingestion not run for this slice"},
        "events": {"found": None, "complete": None, "coverage_percent": None, "status": "unavailable", "reason": "Event completeness requires detail ingestion for every fixture"},
        "quality": {"uniqueness_fixture_duplicate_source_rows": duplicate_fixture_ids, "latest_sync_utc": latest_sync.isoformat() if latest_sync else None, "freshness_hours": age_hours},
    }
