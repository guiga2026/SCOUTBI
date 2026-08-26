from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from sports_bi.app.config import get_settings
from sports_bi.app.database import create_tables, get_db
from sports_bi.app.models import Competition, Coverage, Fixture, Season, Team

settings = get_settings()
app = FastAPI(title="Sports BI API", version="0.1.0", description="API historica de futebol brasileiro")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"
    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=1).ping()
        redis_status = "ok"
    except Exception:
        redis_status = "error"
    status = "healthy" if database == "ok" and redis_status == "ok" else "degraded"
    return {"api": "ok", "database": database, "redis": redis_status, "status": status}


@app.get("/api/v1/competitions")
def competitions(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [{"id": item.id, "name": item.name, "country": item.country, "logo": item.logo, "type": item.type} for item in db.query(Competition).order_by(Competition.name).all()]


@app.get("/api/v1/teams")
def teams(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [{"id": item.id, "name": item.name, "code": item.code, "country": item.country, "logo": item.logo} for item in db.query(Team).order_by(Team.name).all()]


@app.get("/api/v1/seasons")
def seasons(competition_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = db.query(Season).order_by(Season.year.desc())
    if competition_id:
        query = query.filter(Season.competition_id == competition_id)
    return [{"id": item.id, "competition_id": item.competition_id, "year": item.year, "start_date": item.start_date, "end_date": item.end_date, "current": item.current} for item in query.all()]


@app.get("/api/v1/coverage")
def coverage(competition_id: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = db.query(Coverage).order_by(Coverage.endpoint)
    if competition_id:
        query = query.filter(Coverage.competition_id == competition_id)
    return [{"competition_id": item.competition_id, "season_id": item.season_id, "endpoint": item.endpoint, "available": item.available, "notes": item.notes} for item in query.all()]


@app.get("/api/v1/fixtures")
def fixtures(status: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = db.query(Fixture).order_by(Fixture.date)
    if status:
        query = query.filter(Fixture.status == status)
    return [{"id": item.id, "date": item.date, "status": item.status, "home_goals": item.home_goals, "away_goals": item.away_goals} for item in query.all()]


@app.get("/api/v1/fixtures/{fixture_id}")
def fixture(fixture_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    item = db.get(Fixture, fixture_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Jogo nao encontrado")
    return {"id": item.id, "date": item.date, "status": item.status, "home_goals": item.home_goals, "away_goals": item.away_goals}