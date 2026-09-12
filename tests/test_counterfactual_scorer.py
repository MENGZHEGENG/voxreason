from __future__ import annotations

from voxreason_public.results import _aggregate_counterfactual_scores, _counterfactual_score


BASE_PLAN = {
    "emotion": "happy",
    "intent": "inform",
    "pitch": "raised",
    "energy": "high",
    "rate": "medium",
    "pause": "short",
    "stance": "positive",
    "emphasis": ["hello"],
}


def test_counterfactual_requires_a_transition_to_the_expected_value() -> None:
    score = _counterfactual_score(
        BASE_PLAN,
        {**BASE_PLAN, "emotion": "neutral"},
        {"emotion": "neutral"},
    )

    assert score["status"] == "ok"
    assert score["required_change_accuracy"] == 1.0
    assert score["preservation_rate"] == 1.0
    assert score["unexpected_change_rate"] == 0.0


def test_counterfactual_does_not_credit_a_preexisting_expected_value() -> None:
    original = {**BASE_PLAN, "emotion": "neutral"}
    score = _counterfactual_score(original, original, {"emotion": "neutral"})

    assert score["required_change_accuracy"] == 0.0
    assert score["consistency_score"] == 0.0


def test_counterfactual_penalizes_changes_to_preserved_slots() -> None:
    score = _counterfactual_score(
        BASE_PLAN,
        {**BASE_PLAN, "emotion": "neutral", "energy": "low"},
        {"emotion": "neutral"},
    )

    assert score["required_change_accuracy"] == 1.0
    assert score["preservation_rate"] < 1.0
    assert score["unexpected_change_rate"] > 0.0
    assert score["consistency_score"] < 1.0


def test_empty_counterfactual_aggregate_is_explicitly_zero_denominator() -> None:
    summary = _aggregate_counterfactual_scores([], n_missing=3)

    assert summary["status"] == "zero_denominator"
    assert summary["n_pairs"] == 0
    assert summary["n_required_slots"] == 0
    assert summary["n_preserved_slots"] == 0
    assert summary["n_missing"] == 3
    assert summary["counterfactual_consistency_score"] == 0.0
