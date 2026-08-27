from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from sports_bi.app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Competition(TimestampMixin, Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)


class Season(TimestampMixin, Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("competition_id", "year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    year: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current: Mapped[bool] = mapped_column(default=False)


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Fixture(TimestampMixin, Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    round: Mapped[str | None] = mapped_column(String(100), nullable=True)
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Player(TimestampMixin, Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    firstname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[str | None] = mapped_column(String(50), nullable=True)


class PlayerStatistic(TimestampMixin, Base):
    __tablename__ = "player_statistics"
    __table_args__ = (UniqueConstraint("fixture_id", "player_id", "metric"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"))
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    metric: Mapped[str] = mapped_column(String(80))
    value: Mapped[str | None] = mapped_column(String(100), nullable=True)


class FixtureEvent(TimestampMixin, Base):
    __tablename__ = "fixture_events"
    __table_args__ = (UniqueConstraint("fixture_id", "time_minute", "team_id", "player_id", "type", "detail"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    time_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    detail: Mapped[str | None] = mapped_column(String(100), nullable=True)


class FixtureStatistic(TimestampMixin, Base):
    __tablename__ = "fixture_statistics"
    __table_args__ = (UniqueConstraint("fixture_id", "team_id", "metric"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    metric: Mapped[str] = mapped_column(String(80))
    value: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Standing(TimestampMixin, Base):
    __tablename__ = "standings"
    __table_args__ = (UniqueConstraint("competition_id", "season_id", "team_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    played: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draws: Mapped[int | None] = mapped_column(Integer, nullable=True)
    losses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_for: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)


class RawIngestion(Base):
    __tablename__ = "raw_ingestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), default="api-football")
    endpoint: Mapped[str] = mapped_column(String(100))
    request_params: Mapped[str] = mapped_column(Text)
    payload: Mapped[str] = mapped_column(Text)
    status_code: Mapped[int] = mapped_column(Integer)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Coverage(TimestampMixin, Base):
    __tablename__ = "coverage"
    __table_args__ = (UniqueConstraint("competition_id", "season_id", "endpoint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"))
    endpoint: Mapped[str] = mapped_column(String(100))
    available: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MetricDefinition(TimestampMixin, Base):
    __tablename__ = "metric_definitions"
    __table_args__ = (UniqueConstraint("metric_key", "version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_key: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50))
    source_type: Mapped[str] = mapped_column(String(30))
    formula: Mapped[str] = mapped_column(Text)
    methodology: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True)


class PlayerSeasonFeature(TimestampMixin, Base):
    __tablename__ = "player_season_features"
    __table_args__ = (UniqueConstraint("player_id", "team_id", "competition_id", "season_id", "metric_key", "metric_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    metric_key: Mapped[str] = mapped_column(String(100))
    metric_version: Mapped[str] = mapped_column(String(20))
    value: Mapped[float | None] = mapped_column(nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[str] = mapped_column(String(20), default="low")
    source_type: Mapped[str] = mapped_column(String(30), default="derived")


class PlayerScoreComponent(TimestampMixin, Base):
    __tablename__ = "player_score_components"
    __table_args__ = (UniqueConstraint("player_id", "competition_id", "season_id", "position_model", "metric_key", "metric_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    position_model: Mapped[str] = mapped_column(String(50))
    metric_key: Mapped[str] = mapped_column(String(100))
    metric_version: Mapped[str] = mapped_column(String(20))
    raw_value: Mapped[float | None] = mapped_column(nullable=True)
    normalized_value: Mapped[float | None] = mapped_column(nullable=True)
    weight: Mapped[float] = mapped_column(default=0.0)
    contribution: Mapped[float | None] = mapped_column(nullable=True)
    explanation: Mapped[str] = mapped_column(Text)


class PlayerScore(TimestampMixin, Base):
    __tablename__ = "player_scores"
    __table_args__ = (UniqueConstraint("player_id", "competition_id", "season_id", "position_model", "metric_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"), nullable=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    position_model: Mapped[str] = mapped_column(String(50))
    metric_version: Mapped[str] = mapped_column(String(20))
    score: Mapped[float | None] = mapped_column(nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="low")
    explanation: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(30), default="model")