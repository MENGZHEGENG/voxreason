#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voxreason_public.results import (  # noqa: E402
    load_model_runs,
    load_source_label_summary,
    summarize_acoustic_anchor,
    summarize_acoustic_rows,
    summarize_construct_validity,
    summarize_model_runs,
    summarize_source_key_holdout_prior,
)


def fmt(value: float) -> str:
    return f"{value:.3f}"


def csv_row(values: list[str]) -> str:
    escaped = []
    for value in values:
        text = str(value)
        if any(char in text for char in [",", '"', "\n"]):
            text = '"' + text.replace('"', '""') + '"'
        escaped.append(text)
    return ",".join(escaped)


def write_model_csv(rows: list[dict[str, object]], path: Path) -> None:
    lines = [csv_row(["model", "evidence_f1", "plan_accuracy", "grounded", "citation_required", "hallucinated_rate"])]
    order = ["Qwen2.5-3B source-labelled SFT", "Qwen2.5-7B source-labelled SFT", "Qwen2.5-7B preference"]
    by_model = {str(row["model"]): row for row in rows}
    for label in order:
        row = by_model[label]
        lines.append(
            csv_row(
                [
                    label,
                    fmt(float(row["evidence_f1_mean"])),
                    fmt(float(row["plan_slot_accuracy_mean"])),
                    fmt(float(row["grounded_score_mean"])),
                    fmt(float(row["citation_required_grounded_score_mean"])),
                    fmt(float(row["hallucinated_evidence_rate_mean"])),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_source_label_csv(summary: dict[str, object], path: Path) -> None:
    pairs = {row["metric"]: row for row in summary["pairwise"]}
    labels = {
        "evidence_f1": "Evidence F1",
        "decisive_cue_recall": "Decisive cue",
        "plan_slot_accuracy": "Plan acc.",
        "grounded_score": "Grounded",
        "citation_required_grounded_score": "Citation req.",
        "hallucinated_evidence_rate": "Halluc. rate",
        "uncited_evidence_rate": "Uncited rate",
    }
    lines = [csv_row(["metric", "text_control", "source_label_upper_bound", "delta"])]
    for metric, label in labels.items():
        row = pairs[metric]
        lines.append(
            csv_row(
                [
                    label,
                    fmt(float(row["baseline_mean"])),
                    fmt(float(row["candidate_mean"])),
                    fmt(float(row["delta_mean"])),
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_acoustic_csv(summary: dict[str, float | int], path: Path) -> None:
    rows = [
        ("Cases", int(summary["cases"])),
        ("Feature rows", int(summary["feature_rows"])),
        ("Duration (s)", float(summary["duration_sec_mean"])),
        ("Silence fraction", float(summary["silence_fraction_mean"])),
        ("Voiced fraction", float(summary["voiced_fraction_mean"])),
        ("Pitch proxy (Hz)", float(summary["rough_pitch_hz_mean"])),
    ]
    lines = [csv_row(["statistic", "value"])]
    for label, value in rows:
        rendered = str(value) if isinstance(value, int) else fmt(value)
        lines.append(csv_row([label, rendered]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    outputs = ROOT / "outputs/results"
    outputs.mkdir(parents=True, exist_ok=True)
    runs = load_model_runs(ROOT)
    model_rows = summarize_model_runs(runs)
    source_label = load_source_label_summary(ROOT)
    acoustic = summarize_acoustic_rows(ROOT)
    acoustic_anchor = summarize_acoustic_anchor(ROOT)
    construct_validity = summarize_construct_validity(ROOT)
    source_key_prior = summarize_source_key_holdout_prior(ROOT)
    write_model_csv(model_rows, outputs / "listener_free_model_results.csv")
    write_source_label_csv(source_label, outputs / "source_label_upper_bound.csv")
    write_acoustic_csv(acoustic, outputs / "acoustic_preflight_summary.csv")
    source_by_id = {row["system_id"]: row for row in source_label["systems"]}
    result = {
        "claim_scope": "listener_free_evidence_grounded_speech_reasoning",
        "model_results": model_rows,
        "source_label": {
            "num_cases": source_label["cases"],
            "paired_cases": source_label["paired_cases"],
            "text_only_control": source_by_id["text_neutral_control"],
            "source_label_upper_bound": source_by_id["source_label_evidence_planner"],
            "construct_validity": construct_validity,
            "source_key_holdout_prior_only": source_key_prior,
            "acoustic_anchor": acoustic_anchor,
            "pairwise": source_label["pairwise"],
        },
        "acoustic_preflight": acoustic,
    }
    out = ROOT / "data/results/public_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    construct_out = ROOT / "data/results/source_label_construct_validity.json"
    construct_out.write_text(json.dumps(construct_validity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_key_prior_out = ROOT / "data/results/source_key_holdout_prior_only.json"
    source_key_prior_out.write_text(json.dumps(source_key_prior, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    anchor_out = ROOT / "data/results/source_label_acoustic_anchor.json"
    anchor_out.write_text(json.dumps(acoustic_anchor, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
