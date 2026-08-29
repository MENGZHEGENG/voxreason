from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
from statistics import mean, pstdev
from collections import Counter, defaultdict
from typing import Iterable

from voxreason_public.benchmark import PLAN_FIELDS, load_split_cases, plan_slot_accuracy


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

ACOUSTIC_ANCHOR_CONTRASTS = (
    ("source_intensity_rms", "metadata.source_intensity", "strong", "normal", "rms"),
    ("source_intensity_peak", "metadata.source_intensity", "strong", "normal", "peak"),
    ("source_intensity_pitch", "metadata.source_intensity", "strong", "normal", "rough_pitch_hz"),
    ("plan_pitch_rough_pitch", "gold_plan.pitch", "raised", "lowered", "rough_pitch_hz"),
    ("plan_energy_rms", "gold_plan.energy", "high", "low", "rms"),
    ("plan_rate_zcr", "gold_plan.rate", "fast", "slow", "zero_crossing_rate"),
)


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


def _feature_by_case(root: Path) -> dict[str, dict[str, object]]:
    paths = sorted((root / "data/results/listener_free_outputs/82940").glob("**/audio_features.public.jsonl"))
    features: dict[str, dict[str, object]] = {}
    for path in paths:
        for row in read_jsonl(path):
            case_id = str(row.get("case_id", "")).strip()
            if not case_id:
                continue
            for feature in row.get("features", []):
                if isinstance(feature, dict) and feature.get("status") == "ok":
                    features.setdefault(case_id, feature)
                    break
    return features


def _nested_value(row: dict[str, object], dotted_path: str) -> str:
    current: object = row
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part, "")
    return str(current).strip().lower()


def _bootstrap_ci(positive_values: list[float], negative_values: list[float], *, seed: int, samples: int) -> tuple[float, float]:
    sampler = random.Random(seed)
    deltas: list[float] = []
    for _sample_index in range(samples):
        positive_sample = [positive_values[sampler.randrange(len(positive_values))] for _sample in range(len(positive_values))]
        negative_sample = [negative_values[sampler.randrange(len(negative_values))] for _sample in range(len(negative_values))]
        deltas.append(mean(positive_sample) - mean(negative_sample))
    deltas.sort()
    return deltas[int(0.025 * (samples - 1))], deltas[int(0.975 * (samples - 1))]


def _auc(positive_values: list[float], negative_values: list[float]) -> float:
    wins = 0.0
    comparisons = 0
    for positive_value in positive_values:
        for negative_value in negative_values:
            comparisons += 1
            if positive_value > negative_value:
                wins += 1.0
            elif positive_value == negative_value:
                wins += 0.5
    return wins / comparisons if comparisons else 0.0


def summarize_acoustic_anchor(root: Path, *, samples: int = 10000, seed: int = 17) -> dict[str, object]:
    cases = load_split_cases(root)
    features = _feature_by_case(root)
    matched_cases = [case for case in cases if str(case.get("case_id", "")).strip() in features]
    contrasts: list[dict[str, object]] = []
    for contrast_index, (contrast_id, label_source, positive_label, negative_label, feature_name) in enumerate(ACOUSTIC_ANCHOR_CONTRASTS):
        positive_values: list[float] = []
        negative_values: list[float] = []
        for case in matched_cases:
            case_id = str(case.get("case_id", "")).strip()
            feature = features[case_id]
            if feature_name not in feature:
                continue
            value = float(feature[feature_name])
            label = _nested_value(case, label_source)
            if label == positive_label:
                positive_values.append(value)
            elif label == negative_label:
                negative_values.append(value)
        ci_low, ci_high = _bootstrap_ci(positive_values, negative_values, seed=seed + contrast_index, samples=samples)
        delta = mean(positive_values) - mean(negative_values)
        contrasts.append(
            {
                "contrast_id": contrast_id,
                "label_source": label_source,
                "positive_label": positive_label,
                "negative_label": negative_label,
                "feature": feature_name,
                "positive_count": len(positive_values),
                "negative_count": len(negative_values),
                "positive_mean": mean(positive_values),
                "negative_mean": mean(negative_values),
                "delta": delta,
                "bootstrap_ci_low": ci_low,
                "bootstrap_ci_high": ci_high,
                "auc": _auc(positive_values, negative_values),
                "direction_supported": delta > 0 and ci_low > 0,
            }
        )
    return {
        "scope": "source_label_acoustic_anchor",
        "cases": len(cases),
        "feature_rows": len(features),
        "matched_cases": len(matched_cases),
        "bootstrap_samples": samples,
        "seed": seed,
        "anchor_ready": len(matched_cases) == len(cases) and all(row["direction_supported"] for row in contrasts),
        "claim_boundary": "Acoustic anchors check label consistency in the source-label split and do not report listener judgments.",
        "contrasts": contrasts,
    }


def load_source_label_summary(root: Path) -> dict[str, object]:
    return read_json(root / "data/results/source_label_statistics.json")


def _cue_label(case: dict[str, object], cue_type: str) -> str:
    cues = case.get("gold_cues", [])
    if not isinstance(cues, list):
        return ""
    for cue in cues:
        if isinstance(cue, dict) and cue.get("cue_type") == cue_type:
            return str(cue.get("label", "")).strip().lower()
    return ""


def _source_key(case: dict[str, object]) -> tuple[str, str]:
    metadata = case.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    emotion = str(metadata.get("source_emotion") or _cue_label(case, "emotion")).strip().lower()
    intensity = str(metadata.get("source_intensity") or _cue_label(case, "intensity")).strip().lower()
    return emotion, intensity


def _plan_signature(plan: dict[str, object]) -> str:
    return json.dumps(plan, ensure_ascii=False, sort_keys=True)


def _majority_plan(cases: list[dict[str, object]]) -> dict[str, object]:
    counts = Counter(_plan_signature(dict(case.get("gold_plan", {}))) for case in cases)
    return dict(json.loads(counts.most_common(1)[0][0])) if counts else {}


def summarize_construct_validity(root: Path) -> dict[str, object]:
    train_cases = load_split_cases(root, "train")
    test_cases = load_split_cases(root, "test")
    all_cases = load_split_cases(root)

    grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for case in train_cases:
        grouped[_source_key(case)][_plan_signature(dict(case.get("gold_plan", {})))] += 1
    lookup = {
        key: dict(json.loads(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]))
        for key, counter in grouped.items()
    }
    fallback = _majority_plan(train_cases)

    exact_matches = 0
    seen_keys = 0
    slot_scores: list[float] = []
    for case in test_cases:
        key = _source_key(case)
        if key in lookup:
            seen_keys += 1
        prediction = lookup.get(key, fallback)
        gold_plan = dict(case.get("gold_plan", {}))
        exact_matches += int(_plan_signature(prediction) == _plan_signature(gold_plan))
        slot_scores.append(plan_slot_accuracy(prediction, gold_plan))

    denominator = len(test_cases) or 1
    scenes = {_cue_label(case, "scene_state") for case in all_cases if _cue_label(case, "scene_state")}
    roles = {_cue_label(case, "speaker_role") for case in all_cases if _cue_label(case, "speaker_role")}
    texts = {str(case.get("target_text", "")).strip() for case in all_cases if str(case.get("target_text", "")).strip()}
    keys = {_source_key(case) for case in all_cases if any(_source_key(case))}

    return {
        "scope": "controlled_source_label_diagnostic",
        "broad_benchmark_ready": False,
        "total_cases": len(all_cases),
        "public_context_audio_rows": sum(1 for case in all_cases if bool(case.get("context_audio"))),
        "unique_target_texts": len(texts),
        "unique_role_labels": len(roles),
        "unique_scene_labels": len(scenes),
        "unique_emotion_intensity_keys": len(keys),
        "train_lookup_keys": len(lookup),
        "ambiguous_train_keys": sum(1 for counter in grouped.values() if len(counter) > 1),
        "test_cases": len(test_cases),
        "test_keys_seen_in_train": seen_keys,
        "lookup_exact_plan_accuracy": exact_matches / denominator,
        "lookup_plan_slot_accuracy": mean(slot_scores) if slot_scores else 0.0,
        "plan_fields": list(PLAN_FIELDS) + ["emphasis"],
    }
