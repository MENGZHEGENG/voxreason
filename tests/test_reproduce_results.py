from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_reproduce_results_generates_expected_outputs() -> None:
    subprocess.run([sys.executable, "scripts/reproduce_results.py"], cwd=ROOT, check=True)

    expected_paths = [
        ROOT / "outputs/results/listener_free_model_results.csv",
        ROOT / "outputs/results/source_label_upper_bound.csv",
        ROOT / "outputs/results/acoustic_preflight_summary.csv",
        ROOT / "data/results/public_summary.json",
        ROOT / "data/results/source_label_construct_validity.json",
        ROOT / "data/results/source_key_holdout_prior_only.json",
        ROOT / "data/results/source_label_acoustic_anchor.json",
    ]
    for path in expected_paths:
        assert path.exists(), path

    summary = json.loads((ROOT / "data/results/public_summary.json").read_text(encoding="utf-8"))
    source = summary["source_label"]
    assert source["num_cases"] == 100
    assert source["source_label_upper_bound"]["plan_slot_accuracy"] == 1.0
    assert source["text_only_control"]["plan_slot_accuracy"] == 0.185
    assert source["source_label_upper_bound"]["decisive_cue_recall"] == 1.0
    assert source["text_only_control"]["decisive_cue_recall"] == 0.0
    assert source["source_label_upper_bound"]["uncited_evidence_rate"] == 0.0
    assert source["text_only_control"]["uncited_evidence_rate"] == 0.25
    assert source["source_label_upper_bound"]["citation_required_grounded_score"] == 1.0
    assert source["text_only_control"]["citation_required_grounded_score"] < source["text_only_control"]["grounded_score"]
    pairwise = {row["metric"]: row for row in source["pairwise"]}
    assert pairwise["decisive_cue_recall"]["delta_mean"] == 1.0
    assert pairwise["uncited_evidence_rate"]["delta_mean"] == -0.25
    construct = source["construct_validity"]
    assert construct["broad_benchmark_ready"] is False
    assert construct["public_context_audio_rows"] == 0
    assert construct["unique_target_texts"] == 2
    assert construct["unique_scene_labels"] == 1
    assert construct["deterministic_source_key_mappings"] == 15
    assert construct["source_key_mapping_count"] == 15
    assert construct["deterministic_source_key_fraction"] == 1.0
    assert construct["max_plans_per_source_key"] == 1
    assert construct["prompt_taxonomy_valid_gold_plans"] == 100
    assert construct["prompt_taxonomy_invalid_gold_plans"] == 0
    assert construct["prompt_taxonomy_valid_fraction"] == 1.0
    assert construct["lookup_exact_plan_accuracy"] == 1.0
    assert construct["leave_key_out_test_cases"] == 16
    assert construct["leave_key_out_heldout_keys"] == 10
    assert construct["leave_key_out_exact_plan_accuracy"] == 0.0
    assert construct["leave_key_out_plan_slot_accuracy"] == 0.2421875
    assert construct["prior_only_field"] == "source_emotion"
    assert construct["prior_only_train_keys"] == 8
    assert construct["prior_only_ambiguous_train_keys"] == 5
    assert construct["prior_only_test_keys_seen_in_train"] == 16
    assert construct["prior_only_exact_plan_accuracy"] == 0.625
    assert construct["prior_only_plan_slot_accuracy"] == 0.953125
    assert construct["prior_only_counterfactual_edits"] == 16
    assert construct["prior_only_counterfactual_consistency_score"] == pytest.approx(0.2)
    source_key_prior = source["source_key_holdout_prior_only"]
    assert source_key_prior["scope"] == "source_key_disjoint_split_measurement"
    assert source_key_prior["train_cases"] == 60
    assert source_key_prior["test_cases"] == 24
    assert source_key_prior["test_keys_seen_in_train"] == 24
    assert source_key_prior["exact_plan_accuracy"] == 2 / 3
    assert source_key_prior["plan_slot_accuracy"] == 0.9583333333333334
    assert source_key_prior["citation_required_grounded_score"] == 0.0
    assert source_key_prior["counterfactual_edits"] == 24
    assert source_key_prior["counterfactual_consistency_score"] == 0.0
    acoustic_anchor = source["acoustic_anchor"]
    assert acoustic_anchor["anchor_ready"] is True
    assert acoustic_anchor["matched_cases"] == 100
    contrasts = {row["contrast_id"]: row for row in acoustic_anchor["contrasts"]}
    assert contrasts["source_intensity_rms"]["delta"] > 0.017
    assert contrasts["source_intensity_rms"]["bootstrap_ci_low"] > 0
    assert contrasts["plan_pitch_rough_pitch"]["delta"] > 48.0
    assert contrasts["plan_pitch_rough_pitch"]["bootstrap_ci_low"] > 0

    models = {row["model"]: row for row in summary["model_results"]}
    assert set(models) == {"Qwen2.5-3B SFT", "Qwen2.5-7B SFT", "Qwen2.5-7B preference"}
    for row in models.values():
        assert 0.0 <= float(row["plan_slot_accuracy_mean"]) <= 1.0
        assert 0.0 <= float(row["citation_required_grounded_score_mean"]) <= 1.0


def test_readme_score_highlights_match_reproduced_summary() -> None:
    subprocess.run([sys.executable, "scripts/reproduce_results.py"], cwd=ROOT, check=True)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    summary = json.loads((ROOT / "data/results/public_summary.json").read_text(encoding="utf-8"))
    source_label = summary["source_label"]
    expected = {
        "Text-only control": source_label["text_only_control"],
        "Source-label upper bound": source_label["source_label_upper_bound"],
    }
    for row in summary["model_results"]:
        expected[str(row["model"])] = row

    pattern = re.compile(
        r"^- (?P<label>[^:]+): evidence F1 `(?P<evidence>\d+\.\d{3})`, "
        r"(?:decisive-cue recall `(?P<decisive>\d+\.\d{3})`, )?"
        r"plan accuracy `(?P<plan>\d+\.\d{3})`, citation-required score `(?P<citation_required>\d+\.\d{3})`, "
        r"hallucinated-evidence rate `(?P<hallucinated>\d+\.\d{3})`\.",
        re.MULTILINE,
    )
    found = {match.group("label"): match.groupdict() for match in pattern.finditer(readme)}

    assert set(found) == set(expected)
    for label, row in expected.items():
        assert found[label]["evidence"] == f"{float(row['evidence_f1'] if 'evidence_f1' in row else row['evidence_f1_mean']):.3f}"
        if "decisive_cue_recall" in row:
            assert found[label]["decisive"] == f"{float(row['decisive_cue_recall']):.3f}"
        else:
            assert found[label]["decisive"] is None
        assert found[label]["plan"] == f"{float(row['plan_slot_accuracy'] if 'plan_slot_accuracy' in row else row['plan_slot_accuracy_mean']):.3f}"
        assert found[label]["citation_required"] == f"{float(row['citation_required_grounded_score'] if 'citation_required_grounded_score' in row else row['citation_required_grounded_score_mean']):.3f}"
        assert found[label]["hallucinated"] == f"{float(row['hallucinated_evidence_rate'] if 'hallucinated_evidence_rate' in row else row['hallucinated_evidence_rate_mean']):.3f}"
    assert "uncited-evidence rate is `0.250` for the text-only control" in readme
