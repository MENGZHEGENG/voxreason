#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voxreason_public.benchmark import build_prompt_rows, gold_prediction, load_split_cases, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VoxReasonBench planner prompts from public case splits.")
    parser.add_argument("--out-dir", default="outputs/benchmark_prompts/source_label")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    report: dict[str, int | str] = {"out_dir": str(out_dir)}
    for split in ("train", "dev", "test"):
        cases = load_split_cases(ROOT, split=split)
        include_targets = split == "train"
        for mode in ("evidence_grounded", "transcript_only"):
            suffix = "sft" if include_targets else "prompts"
            out_path = out_dir / f"{split}_{mode}_{suffix}.jsonl"
            rows = build_prompt_rows(cases, mode=mode, include_targets=include_targets)
            write_jsonl(out_path, rows)
            report[f"{split}_{mode}_{suffix}"] = len(rows)
        if split != "train":
            gold_path = out_dir / f"{split}_gold_predictions.jsonl"
            write_jsonl(gold_path, [gold_prediction(case) for case in cases])
            report[f"{split}_gold_predictions"] = len(cases)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
