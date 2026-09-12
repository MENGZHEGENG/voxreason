from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from run_evidence_sensitivity import (  # noqa: E402
    build_counterfactual_case,
    build_manifest,
    build_pairs,
    make_prediction,
    summarize_records,
)
from audit_experiment_coverage import audit_experiment  # noqa: E402


def _fixture_case() -> dict[str, object]:
    return {
        "case_id": "case_a",
        "context_text": "A context.",
        "target_text": "Target.",
        "role_profile": "speaker",
        "context_audio": [],
        "metadata": {"source_emotion": "happy", "source_intensity": "strong"},
        "gold_cues": [
            {
                "cue_id": "case_a_emotion",
                "cue_type": "emotion",
                "source": "context_audio",
                "label": "happy",
                "text": "happy",
            }
        ],
        "gold_plan": {
            "emotion": "happy",
            "intent": "inform",
            "pitch": "raised",
            "energy": "high",
            "rate": "medium",
            "pause": "short",
            "emphasis": ["happy"],
            "stance": "positive",
        },
        "counterfactuals": [
            {
                "edit_id": "case_a_emotion_to_neutral",
                "changed_cue_id": "case_a_emotion",
                "expected_plan_delta": {"emotion": "neutral", "energy": "medium", "stance": "neutral"},
            }
        ],
    }


def test_build_pairs_preserves_pair_id_and_source_group() -> None:
    pairs = build_pairs([_fixture_case()])
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair["pair_id"] == "case_a:case_a_emotion_to_neutral"
    assert pair["source_group"] == "happy:strong"
    assert pair["original_case_id"] == "case_a"
    assert pair["counterfactual_case_id"].endswith(":cf")

    cf_case = build_counterfactual_case(_fixture_case(), _fixture_case()["counterfactuals"][0])
    assert cf_case["case_id"] == "case_a:case_a_emotion_to_neutral:cf"
    assert cf_case["gold_plan"]["emotion"] == "neutral"
    assert cf_case["gold_plan"]["energy"] == "medium"


def test_manifest_declares_case_groups_and_denominators() -> None:
    manifest = build_manifest(
        split_id="test_split",
        cases=[_fixture_case()],
        conditions=("prior_only",),
        seeds=(0, 1, 2),
    )
    assert manifest["split_id"] == "test_split"
    assert manifest["seeds"] == [0, 1, 2]
    assert manifest["case_ids"] == ["case_a"]
    assert manifest["case_groups"] == {"case_a": "happy:strong"}
    assert manifest["conditions"]["prior_only"]["metric_denominators"]["pairs"] == 1


def test_summary_reports_total_valid_and_missing_denominators() -> None:
    case = _fixture_case()
    pair = build_pairs([case])[0]
    original = make_prediction(case, "prior_only", seed=0, train_cases=[])
    cf_case = build_counterfactual_case(case, case["counterfactuals"][0])
    records = [
        {
            "condition": "prior_only",
            "seed": 0,
            "pair_id": pair["pair_id"],
            "case_id": case["case_id"],
            "counterfactual_case_id": cf_case["case_id"],
            "source_group": pair["source_group"],
            "prediction_status": "complete",
            "original_prediction": original,
            "counterfactual_prediction": None,
            "ordinary_metrics": {},
            "required_change_metrics": {},
            "preservation_metrics": {},
            "error_reason": "missing counterfactual prediction",
        }
    ]
    summary = summarize_records(records, bootstrap_samples=20, bootstrap_seed=0)
    row = summary["conditions"]["prior_only"]["seeds"]["0"]
    assert row["n_total"] == 1
    assert row["n_valid"] == 0
    assert row["n_missing"] == 1
    assert row["status"] == "incomplete"


def test_counterfactual_records_require_pair_ids_and_split_groups(tmp_path: Path) -> None:
    manifest = build_manifest("test_split", [_fixture_case()], ("prior_only",), (0,))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert manifest["case_groups"]["case_a"] == "happy:strong"

    bad = copy.deepcopy(manifest)
    bad["case_groups"]["case_a"] = "other:group"
    assert bad["case_groups"]["case_a"] != manifest["case_groups"]["case_a"]


def _complete_record(case: dict[str, object] | None = None) -> dict[str, object]:
    case = case or _fixture_case()
    pair = build_pairs([case])[0]
    prediction = make_prediction(case, "prior_only", seed=0, train_cases=[])
    cf_case = build_counterfactual_case(case, case["counterfactuals"][0])
    cf_prediction = make_prediction(
        cf_case,
        "prior_only",
        seed=0,
        train_cases=[],
        counterfactual=True,
        expected_delta=pair["expected_plan_delta"],
    )
    return {
        "condition": "prior_only",
        "seed": 0,
        "pair_id": pair["pair_id"],
        "case_id": case["case_id"],
        "original_case_id": case["case_id"],
        "counterfactual_case_id": cf_case["case_id"],
        "source_group": pair["source_group"],
        "prediction_status": "complete",
        "original_prediction": prediction,
        "counterfactual_prediction": cf_prediction,
        "ordinary_metrics": {"original": {"plan_slot_accuracy": 0.5}, "counterfactual": {"plan_slot_accuracy": 0.25}},
        "required_change_metrics": {
            "status": "ok",
            "required_change_accuracy": 0.0,
            "n_required_slots": 3,
        },
        "preservation_metrics": {
            "status": "ok",
            "preservation_rate": 1.0,
            "unexpected_change_rate": 0.0,
            "consistency_score": 0.5,
        },
        "error_reason": "",
    }


def test_audit_rejects_duplicate_rows_and_split_group_leakage() -> None:
    case = _fixture_case()
    manifest = build_manifest("test_split", [case], ("prior_only",), (0,))
    manifest["pairs"] = [
        {
            "pair_id": manifest["pair_ids"][0],
            "original_case_id": "case_a",
            "counterfactual_case_id": "case_a:case_a_emotion_to_neutral:cf",
            "source_group": "happy:strong",
        }
    ]
    manifest["split_case_groups"] = {
        "train": {"train_case": "happy:strong"},
        "dev": {},
        "test": {"case_a": "happy:strong"},
    }
    record = _complete_record()
    report = audit_experiment(manifest, [record, copy.deepcopy(record)])
    assert report["ok"] is False
    assert any("duplicate" in error for error in report["errors"])
    assert any("cross" in error for error in report["errors"])


def test_summary_bootstraps_each_pair_metric_from_its_declared_section() -> None:
    record = _complete_record()
    summary = summarize_records([record], bootstrap_samples=5, bootstrap_seed=0)
    intervals = summary["conditions"]["prior_only"]["seeds"]["0"]["bootstrap_intervals"]

    assert intervals["required_change_accuracy"]["mean"] == 0.0
    assert intervals["preservation_rate"]["mean"] == 1.0
    assert intervals["unexpected_change_rate"]["mean"] == 0.0
    assert intervals["consistency_score"]["mean"] == 0.5


def test_audit_requires_missing_rows_and_checks_summary_counts() -> None:
    case = _fixture_case()
    manifest = build_manifest("test_split", [case], ("prior_only",), (0,))
    manifest["pairs"] = [
        {
            "pair_id": manifest["pair_ids"][0],
            "original_case_id": "case_a",
            "counterfactual_case_id": "case_a:case_a_emotion_to_neutral:cf",
            "source_group": "happy:strong",
        }
    ]
    manifest["split_case_groups"] = {"train": {}, "dev": {}, "test": {"case_a": "happy:strong"}}
    record = _complete_record()
    summary = {"record_count": 0, "conditions": {"prior_only": {"seeds": {"0": {"n_total": 0, "n_valid": 0}}}}}
    report = audit_experiment(manifest, [], summary)
    assert report["ok"] is False
    assert any("missing expected" in error for error in report["errors"])
    report = audit_experiment(manifest, [record], summarize_records([record], bootstrap_samples=5, bootstrap_seed=0))
    assert report["ok"] is True
