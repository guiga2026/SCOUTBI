from dataclasses import dataclass

from sqlalchemy import select

from sports_bi.app.database import SessionLocal, create_tables
from sports_bi.app.models import MetricDefinition


@dataclass(frozen=True)
class MetricSpec:
    key: str
    name: str
    category: str
    formula: str
    methodology: str
    source_type: str = "derived"
    version: str = "1.0"


METRICS = (
    MetricSpec("goals_per_90", "Goals per 90", "finishing", "goals / minutes * 90", "Only computed when minutes are available."),
    MetricSpec("shots_per_90", "Shots per 90", "finishing", "shots / minutes * 90", "Only computed when shots and minutes are available."),
    MetricSpec("progression_index", "Progression Index", "progression", "progressive_actions / minutes * 90", "Placeholder contract; requires progressive event data."),
    MetricSpec("creation_index", "Creation Index", "creation", "weighted key passes + assists + xA", "Computed only from metrics available in the source."),
    MetricSpec("defensive_index", "Defensive Index", "defense", "weighted tackles + interceptions + recoveries", "Context-free baseline; contextual model is a later version."),
    MetricSpec("consistency", "Consistency", "reliability", "1 - coefficient of variation", "Requires multiple match observations."),
    MetricSpec("scouting_score", "Scouting Score", "scouting", "weighted position model components", "Explainable aggregate of versioned components; never a provider fact."),
    MetricSpec("potential_score", "Potential Score", "potential", "age + trend + performance + sample confidence", "Requires longitudinal observations and sufficient sample."),
    MetricSpec("market_opportunity_score", "Market Opportunity Score", "market", "performance + potential relative to market value", "Unavailable until a licensed market-value source is integrated."),
)


POSITION_MODELS: dict[str, dict[str, float]] = {
    "goalkeeper": {"shot_stopping": 0.30, "distribution": 0.20, "sweeping": 0.15, "cross_management": 0.15, "decision_making": 0.20},
    "center_back": {"defensive": 0.30, "progression": 0.20, "aerial": 0.20, "possession": 0.15, "decision_making": 0.15},
    "full_back": {"defensive": 0.20, "progression": 0.20, "creation": 0.20, "ball_carrying": 0.20, "transition": 0.20},
    "midfielder": {"progression": 0.20, "creation": 0.25, "possession": 0.20, "defensive": 0.15, "decision_making": 0.20},
    "forward": {"finishing": 0.25, "creation": 0.15, "movement": 0.20, "progression": 0.15, "efficiency": 0.25},
}


def seed_metric_definitions() -> int:
    create_tables()
    inserted = 0
    with SessionLocal.begin() as session:
        for spec in METRICS:
            existing = session.scalar(select(MetricDefinition).where(MetricDefinition.metric_key == spec.key, MetricDefinition.version == spec.version))
            if existing is None:
                session.add(MetricDefinition(metric_key=spec.key, version=spec.version, name=spec.name, category=spec.category, source_type=spec.source_type, formula=spec.formula, methodology=spec.methodology))
                inserted += 1
    return inserted
