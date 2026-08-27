from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable


METRICS = (
    "evidence_f1",
    "plan_slot_accuracy",
    "grounded_score",
    "hallucinated_evidence_rate",
)

MODEL_LABELS = {
    "82938": "Qwen2.5-3B SFT",
    "82939": "Qwen2.5-7B SFT",
    "82941": "Qwen2.5-7B preference",
}


@dataclass(frozen=True)
class ModelRun:
    group: str
    seed: str
    metrics: dict[str, float]
    predictions: int
    missing_predictions: int


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_model_runs(root: Path) -> list[ModelRun]:
    runs: list[ModelRun] = []
    for path in sorted((root / "data/results/listener_free_outputs").glob("*/**/eval_summary.json")):
        job_id = path.relative_to(root / "data/results/listener_free_outputs").parts[0]
        if job_id not in MODEL_LABELS:
            continue
        payload = read_json(path)
        runs.append(
            ModelRun(
                group=MODEL_LABELS[job_id],
                seed=path.parent.parent.name,
                metrics={metric: float(payload[metric]) for metric in METRICS},
                predictions=int(payload.get("num_predictions", 0)),
                missing_predictions=int(payload.get("missing_predictions", 0)),
            )
        )
    return runs


def summarize_model_runs(runs: Iterable[ModelRun]) -> list[dict[str, object]]:
    grouped: dict[str, list[ModelRun]] = {}
    for run in runs:
        grouped.setdefault(run.group, []).append(run)
    summaries: list[dict[str, object]] = []
    for group, members in sorted(grouped.items()):
        row: dict[str, object] = {
            "model": group,
            "seeds": len(members),
            "predictions": sum(item.predictions for item in members),
            "missing_predictions": sum(item.missing_predictions for item in members),
        }
        for metric in METRICS:
            values = [item.metrics[metric] for item in members]
            row[f"{metric}_mean"] = mean(values)
            row[f"{metric}_std"] = pstdev(values) if len(values) > 1 else 0.0
        summaries.append(row)
    return summaries


def summarize_acoustic_rows(root: Path) -> dict[str, float | int]:
    paths = sorted((root / "data/results/listener_free_outputs/82940").glob("**/audio_features.public.jsonl"))
    rows = [row for path in paths for row in read_jsonl(path)]
    feature_rows = [feature for row in rows for feature in row.get("features", []) if feature.get("status") == "ok"]
    summary: dict[str, float | int] = {"cases": len(rows), "feature_rows": len(feature_rows)}
    for key in ("duration_sec", "silence_fraction", "voiced_fraction", "rough_pitch_hz", "zero_crossing_rate"):
        values = [float(feature[key]) for feature in feature_rows if key in feature]
        summary[f"{key}_mean"] = mean(values) if values else 0.0
    return summary


def load_source_label_summary(root: Path) -> dict[str, object]:
    return read_json(root / "data/results/source_label_statistics.json")
