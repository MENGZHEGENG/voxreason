from __future__ import annotations

import json
from pathlib import Path
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
    ]
    for path in expected_paths:
        assert path.exists(), path

    summary = json.loads((ROOT / "data/results/public_summary.json").read_text(encoding="utf-8"))
    source = summary["source_label"]
    assert source["num_cases"] == 100
    assert source["evidence_grounded"]["plan_slot_accuracy"] == 1.0
    assert source["text_only_control"]["plan_slot_accuracy"] == 0.185

    models = {row["model"]: row for row in summary["model_results"]}
    assert set(models) == {"Qwen2.5-3B SFT", "Qwen2.5-7B SFT", "Qwen2.5-7B preference"}
    assert models["Qwen2.5-3B SFT"]["plan_slot_accuracy_mean"] > models["Qwen2.5-7B preference"]["plan_slot_accuracy_mean"]
