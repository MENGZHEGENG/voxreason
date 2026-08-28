from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_reproduce_results_generates_expected_outputs() -> None:
    subprocess.run([sys.executable, "scripts/reproduce_results.py"], cwd=ROOT, check=True)

    expected_paths = [
        ROOT / "paper/tables/listener_free_model_results.tex",
        ROOT / "paper/tables/source_label_upper_bound.tex",
        ROOT / "paper/tables/acoustic_preflight_summary.tex",
        ROOT / "data/results/public_summary.json",
        ROOT / "data/results/source_label_construct_validity.json",
    ]
    for path in expected_paths:
        assert path.exists(), path

    summary = json.loads((ROOT / "data/results/public_summary.json").read_text(encoding="utf-8"))
    source = summary["source_label"]
    assert source["num_cases"] == 100
    assert source["evidence_grounded"]["plan_slot_accuracy"] == 1.0
    assert source["text_only_control"]["plan_slot_accuracy"] == 0.185
    construct = source["construct_validity"]
    assert construct["broad_benchmark_ready"] is False
    assert construct["public_context_audio_rows"] == 0
    assert construct["unique_target_texts"] == 2
    assert construct["unique_scene_labels"] == 1
    assert construct["lookup_exact_plan_accuracy"] == 1.0

    models = {row["model"]: row for row in summary["model_results"]}
    assert set(models) == {"Qwen2.5-3B SFT", "Qwen2.5-7B SFT", "Qwen2.5-7B preference"}
    for row in models.values():
        assert 0.0 <= float(row["plan_slot_accuracy_mean"]) <= 1.0


def test_readme_score_highlights_match_reproduced_summary() -> None:
    subprocess.run([sys.executable, "scripts/reproduce_results.py"], cwd=ROOT, check=True)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    summary = json.loads((ROOT / "data/results/public_summary.json").read_text(encoding="utf-8"))
    source_label = summary["source_label"]
    expected = {
        "Text-only control": source_label["text_only_control"],
        "Evidence-grounded planner": source_label["evidence_grounded"],
    }
    for row in summary["model_results"]:
        expected[str(row["model"])] = row

    pattern = re.compile(
        r"^- (?P<label>[^:]+): evidence F1 `(?P<evidence>\d+\.\d{3})`, "
        r"plan accuracy `(?P<plan>\d+\.\d{3})`, grounded score `(?P<grounded>\d+\.\d{3})`, "
        r"hallucinated-evidence rate `(?P<hallucinated>\d+\.\d{3})`\.",
        re.MULTILINE,
    )
    found = {match.group("label"): match.groupdict() for match in pattern.finditer(readme)}

    assert set(found) == set(expected)
    for label, row in expected.items():
        assert found[label]["evidence"] == f"{float(row['evidence_f1'] if 'evidence_f1' in row else row['evidence_f1_mean']):.3f}"
        assert found[label]["plan"] == f"{float(row['plan_slot_accuracy'] if 'plan_slot_accuracy' in row else row['plan_slot_accuracy_mean']):.3f}"
        assert found[label]["grounded"] == f"{float(row['grounded_score'] if 'grounded_score' in row else row['grounded_score_mean']):.3f}"
        assert found[label]["hallucinated"] == f"{float(row['hallucinated_evidence_rate'] if 'hallucinated_evidence_rate' in row else row['hallucinated_evidence_rate_mean']):.3f}"
