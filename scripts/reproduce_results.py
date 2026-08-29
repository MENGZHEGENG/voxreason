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
)


def fmt(value: float) -> str:
    return f"{value:.3f}"


def tex_row(values: list[str]) -> str:
    return " & ".join(values) + r" \\"


def write_model_table(rows: list[dict[str, object]], path: Path) -> None:
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        tex_row(["Model", "Evidence F1", "Plan acc.", "Grounded", "Halluc. rate"]),
        r"\midrule",
    ]
    order = ["Qwen2.5-3B SFT", "Qwen2.5-7B SFT", "Qwen2.5-7B preference"]
    by_model = {str(row["model"]): row for row in rows}
    for label in order:
        row = by_model[label]
        lines.append(
            tex_row(
                [
                    label,
                    fmt(float(row["evidence_f1_mean"])),
                    fmt(float(row["plan_slot_accuracy_mean"])),
                    fmt(float(row["grounded_score_mean"])),
                    fmt(float(row["hallucinated_evidence_rate_mean"])),
                ]
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_source_label_table(summary: dict[str, object], path: Path) -> None:
    pairs = {row["metric"]: row for row in summary["pairwise"]}
    labels = {
        "evidence_f1": "Evidence F1",
        "plan_slot_accuracy": "Plan acc.",
        "grounded_score": "Grounded",
        "hallucinated_evidence_rate": "Halluc. rate",
    }
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        tex_row(["Metric", "Text control", "Source-label upper bound", r"$\Delta$"]),
        r"\midrule",
    ]
    for metric, label in labels.items():
        row = pairs[metric]
        lines.append(
            tex_row(
                [
                    label,
                    fmt(float(row["baseline_mean"])),
                    fmt(float(row["candidate_mean"])),
                    fmt(float(row["delta_mean"])),
                ]
            )
        )
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_acoustic_table(summary: dict[str, float | int], path: Path) -> None:
    rows = [
        ("Cases", int(summary["cases"])),
        ("Feature rows", int(summary["feature_rows"])),
        ("Duration (s)", float(summary["duration_sec_mean"])),
        ("Silence fraction", float(summary["silence_fraction_mean"])),
        ("Voiced fraction", float(summary["voiced_fraction_mean"])),
        ("Pitch proxy (Hz)", float(summary["rough_pitch_hz_mean"])),
    ]
    lines = [r"\begin{tabular}{lr}", r"\toprule", tex_row(["Statistic", "Value"]), r"\midrule"]
    for label, value in rows:
        rendered = str(value) if isinstance(value, int) else fmt(value)
        lines.append(tex_row([label, rendered]))
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    tables = ROOT / "paper/tables"
    tables.mkdir(parents=True, exist_ok=True)
    runs = load_model_runs(ROOT)
    model_rows = summarize_model_runs(runs)
    source_label = load_source_label_summary(ROOT)
    acoustic = summarize_acoustic_rows(ROOT)
    acoustic_anchor = summarize_acoustic_anchor(ROOT)
    construct_validity = summarize_construct_validity(ROOT)
    write_model_table(model_rows, tables / "listener_free_model_results.tex")
    write_source_label_table(source_label, tables / "source_label_upper_bound.tex")
    write_acoustic_table(acoustic, tables / "acoustic_preflight_summary.tex")
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
    anchor_out = ROOT / "data/results/source_label_acoustic_anchor.json"
    anchor_out.write_text(json.dumps(acoustic_anchor, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
