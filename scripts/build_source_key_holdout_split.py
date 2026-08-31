#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
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


def source_key(case: dict[str, Any]) -> tuple[str, str]:
    metadata = case.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    emotion = str(metadata.get("source_emotion", "")).strip().lower()
    intensity = str(metadata.get("source_intensity", "")).strip().lower()
    return emotion, intensity


def load_cases(split_dir: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for split in SPLITS:
        cases.extend(read_jsonl(split_dir / f"{split}_cases_public.jsonl"))
    return cases


def ordered_keys(cases: list[dict[str, Any]], seed: int) -> list[tuple[str, str]]:
    keys = {source_key(case) for case in cases if any(source_key(case))}
    return sorted(keys, key=lambda key: (hashlib.sha256(f"{seed}:{key[0]}:{key[1]}".encode("utf-8")).hexdigest(), key))


def split_by_source_key(cases: list[dict[str, Any]], *, seed: int, dev_keys: int, test_keys: int) -> dict[str, list[dict[str, Any]]]:
    keys = ordered_keys(cases, seed)
    if dev_keys < 1 or test_keys < 1 or dev_keys + test_keys >= len(keys):
        raise ValueError("dev_keys and test_keys must leave at least one source key for training")
    dev_key_set = set(keys[:dev_keys])
    test_key_set = set(keys[dev_keys : dev_keys + test_keys])
    train_key_set = set(keys[dev_keys + test_keys :])
    by_split = {split: [] for split in SPLITS}
    for case in sorted(cases, key=lambda row: str(row.get("case_id", ""))):
        key = source_key(case)
        if key in dev_key_set:
            by_split["dev"].append(case)
        elif key in test_key_set:
            by_split["test"].append(case)
        elif key in train_key_set:
            by_split["train"].append(case)
        else:
            raise ValueError(f"case has unknown source key: {key}")
    return by_split


def key_rows(by_split: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    return {
        split: [f"{emotion}:{intensity}" for emotion, intensity in sorted({source_key(case) for case in cases})]
        for split, cases in by_split.items()
    }


def overlaps(by_split: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    keys = {split: {source_key(case) for case in cases} for split, cases in by_split.items()}
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-key holdout split for VoxReasonBench source-label cases.")
    parser.add_argument("--source-split-dir", default="data/benchmark/source_label/splits")
    parser.add_argument("--out-dir", default="data/benchmark/source_label/source_key_holdout")
    parser.add_argument("--seed", type=int, default=20260829)
    parser.add_argument("--dev-keys", type=int, default=3)
    parser.add_argument("--test-keys", type=int, default=3)
    args = parser.parse_args()

    source_split_dir = ROOT / args.source_split_dir
    out_dir = ROOT / args.out_dir
    split_dir = out_dir / "splits"
    cases = load_cases(source_split_dir)
    case_check = validate_cases(cases)
    if case_check["issue_count"]:
        print(json.dumps(case_check, indent=2, sort_keys=True))
        raise SystemExit(1)

    by_split = split_by_source_key(cases, seed=args.seed, dev_keys=args.dev_keys, test_keys=args.test_keys)
    for split, split_cases in by_split.items():
        write_jsonl(split_dir / f"{split}_cases_public.jsonl", split_cases)
    prompt_counts = write_prompt_files(out_dir, by_split)
    overlap_counts = overlaps(by_split)
    summary = {
        "split_id": "voxreason_source_key_holdout_v1",
        "source": str(source_split_dir.relative_to(ROOT)),
        "seed": args.seed,
        "dev_source_keys": args.dev_keys,
        "test_source_keys": args.test_keys,
        "case_count": len(cases),
        "split_case_counts": {split: len(rows) for split, rows in by_split.items()},
        "split_source_keys": key_rows(by_split),
        "source_key_overlap_counts": overlap_counts,
        "heldout_ready": all(count == 0 for count in overlap_counts.values()),
        "prompt_counts": prompt_counts,
        "claim_boundary": "This split tests source-key transfer for automatic planner measurements only; it does not report listener judgments or waveform user ratings.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
