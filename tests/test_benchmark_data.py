from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from voxreason_public.benchmark import load_split_cases, score_prediction, validate_cases


ROOT = Path(__file__).resolve().parents[1]


def test_public_benchmark_cases_are_complete_and_clean() -> None:
    cases = load_split_cases(ROOT)
    report = validate_cases(cases)

    assert report["case_count"] == 100
    assert report["issues"] == []


def test_public_benchmark_splits_match_expected_counts() -> None:
    assert len(load_split_cases(ROOT, split="train")) == 67
    assert len(load_split_cases(ROOT, split="dev")) == 17
    assert len(load_split_cases(ROOT, split="test")) == 16


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_key(row: dict[str, object]) -> tuple[str, str]:
    metadata = row.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    return (str(metadata.get("source_emotion", "")).lower(), str(metadata.get("source_intensity", "")).lower())


def test_source_key_holdout_split_is_key_disjoint() -> None:
    subprocess.run([sys.executable, "scripts/build_source_key_holdout_split.py"], cwd=ROOT, check=True)

    holdout_root = ROOT / "data/benchmark/source_label/source_key_holdout"
    split_cases = {split: read_jsonl(holdout_root / "splits" / f"{split}_cases_public.jsonl") for split in ("train", "dev", "test")}
    keys = {split: {source_key(row) for row in rows} for split, rows in split_cases.items()}
    summary = json.loads((holdout_root / "summary.json").read_text(encoding="utf-8"))

    assert {split: len(rows) for split, rows in split_cases.items()} == {"train": 60, "dev": 16, "test": 24}
    assert keys["train"].isdisjoint(keys["dev"])
    assert keys["train"].isdisjoint(keys["test"])
    assert keys["dev"].isdisjoint(keys["test"])
    assert summary["heldout_ready"] is True
    assert summary["source_key_overlap_counts"] == {"dev_test": 0, "train_dev": 0, "train_test": 0}
    assert validate_cases([row for rows in split_cases.values() for row in rows])["issues"] == []


def test_gold_predictions_score_perfectly() -> None:
    cases = {case["case_id"]: case for case in load_split_cases(ROOT, split="test")}
    gold_rows = []
    for line in (ROOT / "data/benchmark/source_label/test_gold_predictions.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            import json

            gold_rows.append(json.loads(line))

    scores = [score_prediction(cases[row["case_id"]], row) for row in gold_rows]
    assert len(scores) == 16
    assert all(score["evidence_f1"] == 1.0 for score in scores)
    assert all(score["decisive_cue_recall"] == 1.0 for score in scores)
    assert all(score["plan_slot_accuracy"] == 1.0 for score in scores)
    assert all(score["grounded_score"] == 1.0 for score in scores)
    assert all(score["uncited_evidence_rate"] == 0.0 for score in scores)


def test_benchmark_scripts_run() -> None:
    subprocess.run([sys.executable, "scripts/validate_benchmark_data.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/check_benchmark_files.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/build_benchmark_prompts.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/build_source_key_holdout_split.py"], cwd=ROOT, check=True)
    subprocess.run(
        [
            sys.executable,
            "scripts/score_predictions.py",
            "data/benchmark/source_label/test_gold_predictions.jsonl",
            "--split",
            "test",
        ],
        cwd=ROOT,
        check=True,
    )
