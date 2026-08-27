from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class ScoreComponent:
    metric_key: str
    raw_value: float
    normalized_value: float
    weight: float
    contribution: float
    explanation: str


@dataclass(frozen=True)
class ScoreResult:
    score: float
    components: tuple[ScoreComponent, ...]
    confidence: str


def percentile_rank(value: float, population: Iterable[float]) -> float | None:
    values = sorted(float(item) for item in population)
    if not values:
        return None
    rank = sum(item <= value for item in values) / len(values)
    return round(rank * 100, 2)


def z_score(value: float, population: Iterable[float]) -> float | None:
    values = [float(item) for item in population]
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    standard_deviation = sqrt(sum((item - mean) ** 2 for item in values) / len(values))
    if standard_deviation == 0:
        return 0.0
    return round((value - mean) / standard_deviation, 4)


def explainable_score(features: Mapping[str, float], weights: Mapping[str, float], sample_size: int, minimum_sample: int = 5) -> ScoreResult | None:
    """Return a weighted 0-100 score only from observed, already-normalized features."""
    available = [(key, float(features[key]), float(weights[key])) for key in weights if key in features and features[key] is not None and weights[key] > 0]
    if not available:
        return None
    total_weight = sum(weight for _, _, weight in available)
    components = tuple(
        ScoreComponent(key, value, value, weight / total_weight, value * weight / total_weight, f"{key} observado e normalizado; peso={weight:g}")
        for key, value, weight in available
    )
    score = round(sum(component.contribution for component in components), 2)
    confidence = "high" if sample_size >= minimum_sample * 3 else "medium" if sample_size >= minimum_sample else "low"
    return ScoreResult(score, components, confidence)
