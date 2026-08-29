#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voxreason_public.benchmark import build_prompt_rows, gold_prediction, read_jsonl, validate_cases, write_jsonl  # noqa: E402

SPLITS = ("train", "dev", "test")
DEFAULT_DEV_EMOTIONS = ("fearful",)
DEFAULT_TEST_EMOTIONS = ("angry", "calm")


def source_emotion(case: dict[str, Any]) -> str:
    metadata = case.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    return str(metadata.get("source_emotion", "")).strip().lower()


def source_key(case: dict[str, Any]) -> tuple[str, str]:
    metadata = case.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    return (
        str(metadata.get("source_emotion", "")).strip().lower(),
        str(metadata.get("source_intensity", "")).strip().lower(),
    )


def load_cases(split_dir: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for split in SPLITS:
        cases.extend(read_jsonl(split_dir / f"{split}_cases_public.jsonl"))
    return cases


def split_by_source_emotion(cases: list[dict[str, Any]], *, dev_emotions: set[str], test_emotions: set[str]) -> dict[str, list[dict[str, Any]]]:
    if not dev_emotions or not test_emotions:
        raise ValueError("dev and test source-emotion sets must be non-empty")
    if dev_emotions & test_emotions:
        raise ValueError("dev and test source-emotion sets must be disjoint")
    by_split = {split: [] for split in SPLITS}
    for case in sorted(cases, key=lambda row: str(row.get("case_id", ""))):
        emotion = source_emotion(case)
        if emotion in dev_emotions:
            by_split["dev"].append(case)
        elif emotion in test_emotions:
            by_split["test"].append(case)
        else:
            by_split["train"].append(case)
    if not all(by_split[split] for split in SPLITS):
        raise ValueError("source-emotion split produced an empty train, dev, or test split")
    return by_split


def emotion_rows(by_split: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    return {split: sorted({source_emotion(case) for case in cases}) for split, cases in by_split.items()}


def source_key_rows(by_split: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    return {
        split: [f"{emotion}:{intensity}" for emotion, intensity in sorted({source_key(case) for case in cases})]
        for split, cases in by_split.items()
    }


def overlaps(by_split: dict[str, list[dict[str, Any]]], key_fn) -> dict[str, int]:
    keys = {split: {key_fn(case) for case in cases} for split, cases in by_split.items()}
    return {
        "train_dev": len(keys["train"] & keys["dev"]),
        "train_test": len(keys["train"] & keys["test"]),
        "dev_test": len(keys["dev"] & keys["test"]),
    }


def write_prompt_files(out_dir: Path, by_split: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for split, cases in by_split.items():
        include_targets = split == "train"
        for mode in ("evidence_grounded", "transcript_only"):
            suffix = "sft" if include_targets else "prompts"
            rows = build_prompt_rows(cases, mode=mode, include_targets=include_targets)
            write_jsonl(out_dir / f"{split}_{mode}_{suffix}.jsonl", rows)
            counts[f"{split}_{mode}_{suffix}"] = len(rows)
        if split != "train":
            write_jsonl(out_dir / f"{split}_gold_predictions.jsonl", [gold_prediction(case) for case in cases])
            counts[f"{split}_gold_predictions"] = len(cases)
    return counts


def parse_csv(value: str) -> set[str]:
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-emotion holdout split for VoxReasonBench source-label cases.")
    parser.add_argument("--source-split-dir", default="data/benchmark/source_label/splits")
    parser.add_argument("--out-dir", default="data/benchmark/source_label/source_emotion_holdout")
    parser.add_argument("--seed", type=int, default=20260830)
    parser.add_argument("--dev-emotions", default=",".join(DEFAULT_DEV_EMOTIONS))
    parser.add_argument("--test-emotions", default=",".join(DEFAULT_TEST_EMOTIONS))
    args = parser.parse_args()

    source_split_dir = ROOT / args.source_split_dir
    out_dir = ROOT / args.out_dir
    split_dir = out_dir / "splits"
    cases = load_cases(source_split_dir)
    case_check = validate_cases(cases)
    if case_check["issue_count"]:
        print(json.dumps(case_check, indent=2, sort_keys=True))
        raise SystemExit(1)

    dev_emotions = parse_csv(args.dev_emotions)
    test_emotions = parse_csv(args.test_emotions)
    by_split = split_by_source_emotion(cases, dev_emotions=dev_emotions, test_emotions=test_emotions)
    for split, split_cases in by_split.items():
        write_jsonl(split_dir / f"{split}_cases_public.jsonl", split_cases)
    prompt_counts = write_prompt_files(out_dir, by_split)
    emotion_overlap_counts = overlaps(by_split, source_emotion)
    source_key_overlap_counts = overlaps(by_split, source_key)
    summary = {
        "split_id": "voxreason_source_emotion_holdout_v1",
        "source": str(source_split_dir.relative_to(ROOT)),
        "seed": args.seed,
        "dev_source_emotions": sorted(dev_emotions),
        "test_source_emotions": sorted(test_emotions),
        "case_count": len(cases),
        "split_case_counts": {split: len(rows) for split, rows in by_split.items()},
        "split_source_emotions": emotion_rows(by_split),
        "split_source_keys": source_key_rows(by_split),
        "source_emotion_overlap_counts": emotion_overlap_counts,
        "source_key_overlap_counts": source_key_overlap_counts,
        "heldout_ready": all(count == 0 for count in emotion_overlap_counts.values()),
        "prompt_counts": prompt_counts,
        "claim_boundary": "This split tests source-emotion transfer for automatic planner diagnostics only; it does not report listener judgments or waveform user ratings.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
