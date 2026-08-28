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

from voxreason_public.benchmark import load_split_cases, read_jsonl, score_prediction, summarize_scores, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Score VoxReasonBench planner predictions.")
    parser.add_argument("predictions", help="JSONL with case_id, cited_cues, and plan fields.")
    parser.add_argument("--split", choices=["train", "dev", "test"], default="test")
    parser.add_argument("--out-dir", default="outputs/evaluation/source_label")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()

    cases = {case["case_id"]: case for case in load_split_cases(ROOT, split=args.split)}
    predictions = read_jsonl(Path(args.predictions))
    predicted_ids = {str(prediction.get("case_id", "")) for prediction in predictions}
    missing = sorted(set(cases) - predicted_ids)
    extra = sorted(predicted_ids - set(cases))
    if missing and not args.allow_missing:
        raise SystemExit(f"Missing predictions for {len(missing)} cases; first missing: {missing[:5]}")
    if extra:
        raise SystemExit(f"Predictions contain unknown case_ids: {extra[:5]}")

    score_rows = []
    for prediction in predictions:
        case_id = str(prediction["case_id"])
        score_rows.append({"case_id": case_id, **score_prediction(cases[case_id], prediction)})
    summary = {
        "split": args.split,
        "num_predictions": len(predictions),
        "missing_predictions": len(missing),
        **summarize_scores(score_rows),
    }

    out_dir = ROOT / args.out_dir
    write_jsonl(out_dir / "scores.jsonl", score_rows)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
