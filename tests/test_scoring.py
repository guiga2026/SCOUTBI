from sports_bi.metrics.scoring import explainable_score, percentile_rank, z_score


def test_percentile_and_z_score_are_deterministic() -> None:
    assert percentile_rank(20, [10, 20, 30]) == 66.67
    assert z_score(20, [10, 20, 30]) == 0.0


def test_score_uses_available_features_and_reports_confidence() -> None:
    result = explainable_score({"creation": 80, "progression": 60}, {"creation": 2, "progression": 1}, sample_size=15)
    assert result is not None
    assert result.score == round((80 * 2 + 60) / 3, 2)
    assert result.confidence == "high"
    assert len(result.components) == 2


def test_score_is_none_without_observed_features() -> None:
    assert explainable_score({}, {"creation": 1}, sample_size=100) is None
