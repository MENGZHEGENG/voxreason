from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
from statistics import mean, pstdev
from collections import Counter, defaultdict
from typing import Iterable

from voxreason_public.benchmark import ALL_PLAN_FIELDS, PLAN_FIELDS, PLAN_SCHEMA, load_split_cases, normalize_label, plan_slot_accuracy


METRICS = (
    "evidence_f1",
    "plan_slot_accuracy",
    "grounded_score",
    "citation_required_grounded_score",
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


def _metric_value(payload: dict, metric: str) -> float:
    if metric in payload:
        return float(payload[metric])
    if metric == "citation_required_grounded_score":
        grounded = float(payload.get("grounded_score", 0.0))
        return grounded * float(payload.get("evidence_recall", 0.0))
    return 0.0


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
                metrics={metric: _metric_value(payload, metric) for metric in METRICS},
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


def _plan_value(plan: dict[str, object], slot: str) -> object:
    return plan.get(slot, ()) if slot == "emphasis" else plan.get(slot, "")


def _values_equal(left: object, right: object) -> bool:
    if isinstance(left, list) or isinstance(right, list):
        left_items = left if isinstance(left, list) else [left]
        right_items = right if isinstance(right, list) else [right]
        return {normalize_label(item) for item in left_items} == {normalize_label(item) for item in right_items}
    return normalize_label(left) == normalize_label(right)


def _changed_plan_slots(before: dict[str, object], after: dict[str, object]) -> set[str]:
    return {field for field in ALL_PLAN_FIELDS if not _values_equal(_plan_value(before, field), _plan_value(after, field))}


def _counterfactual_score(original_plan: dict[str, object], counterfactual_plan: dict[str, object], expected_delta: dict[str, object]) -> tuple[float, float, float]:
    expected_slots = set(expected_delta)
    observed_changes = _changed_plan_slots(original_plan, counterfactual_plan)
    expected_hits = sum(1 for slot, expected in expected_delta.items() if _values_equal(_plan_value(counterfactual_plan, slot), expected))
    expected_change_accuracy = expected_hits / len(expected_slots) if expected_slots else 1.0
    stable_slots = set(ALL_PLAN_FIELDS) - expected_slots
    unexpected_change_rate = len(observed_changes - expected_slots) / len(stable_slots) if stable_slots else 0.0
    return expected_change_accuracy, unexpected_change_rate, max(0.0, expected_change_accuracy * (1.0 - unexpected_change_rate))


def _prompt_taxonomy_coverage(cases: list[dict[str, object]]) -> tuple[int, int, float]:
    choices = {
        field: set(str(value).split("|"))
        for field, value in PLAN_SCHEMA["plan"].items()
        if isinstance(value, str)
    }
    valid = 0
    for case in cases:
        plan = case.get("gold_plan", {})
        if not isinstance(plan, dict):
            continue
        if all(str(plan.get(field, "")).strip().lower() in allowed for field, allowed in choices.items()):
            valid += 1
    denominator = len(cases) or 1
    return valid, len(cases) - valid, valid / denominator


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
    prior_grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for case in train_cases:
        emotion = _source_key(case)[0]
        if emotion:
            prior_grouped[emotion][_plan_signature(dict(case.get("gold_plan", {})))] += 1
    prior_lookup = {
        emotion: dict(json.loads(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]))
        for emotion, counter in prior_grouped.items()
    }
    fallback = _majority_plan(train_cases)

    exact_matches = 0
    seen_keys = 0
    slot_scores: list[float] = []
    key_holdout_exact_matches = 0
    key_holdout_slot_scores: list[float] = []
    prior_exact_matches = 0
    prior_seen_keys = 0
    prior_slot_scores: list[float] = []
    prior_cf_expected_scores: list[float] = []
    prior_cf_unexpected_scores: list[float] = []
    prior_cf_consistency_scores: list[float] = []
    heldout_keys: set[tuple[str, str]] = set()
    for case in test_cases:
        key = _source_key(case)
        emotion = key[0]
        heldout_keys.add(key)
        if key in lookup:
            seen_keys += 1
        prediction = lookup.get(key, fallback)
        gold_plan = dict(case.get("gold_plan", {}))
        exact_matches += int(_plan_signature(prediction) == _plan_signature(gold_plan))
        slot_scores.append(plan_slot_accuracy(prediction, gold_plan))

        if emotion in prior_lookup:
            prior_seen_keys += 1
        prior_prediction = prior_lookup.get(emotion, fallback)
        prior_exact_matches += int(_plan_signature(prior_prediction) == _plan_signature(gold_plan))
        prior_slot_scores.append(plan_slot_accuracy(prior_prediction, gold_plan))
        for counterfactual in case.get("counterfactuals", []):
            if not isinstance(counterfactual, dict):
                continue
            expected_delta = counterfactual.get("expected_plan_delta", {})
            if not isinstance(expected_delta, dict):
                continue
            counterfactual_emotion = normalize_label(expected_delta.get("emotion", emotion))
            counterfactual_prediction = prior_lookup.get(counterfactual_emotion, fallback)
            expected_score, unexpected_rate, consistency = _counterfactual_score(prior_prediction, counterfactual_prediction, expected_delta)
            prior_cf_expected_scores.append(expected_score)
            prior_cf_unexpected_scores.append(unexpected_rate)
            prior_cf_consistency_scores.append(consistency)

        reduced_train = [row for row in train_cases if _source_key(row) != key]
        reduced_grouped: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        for train_case in reduced_train:
            reduced_grouped[_source_key(train_case)][_plan_signature(dict(train_case.get("gold_plan", {})))] += 1
        reduced_lookup = {
            reduced_key: dict(json.loads(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]))
            for reduced_key, counter in reduced_grouped.items()
        }
        reduced_fallback = _majority_plan(reduced_train or train_cases)
        key_holdout_prediction = reduced_lookup.get(key, reduced_fallback)
        key_holdout_exact_matches += int(_plan_signature(key_holdout_prediction) == _plan_signature(gold_plan))
        key_holdout_slot_scores.append(plan_slot_accuracy(key_holdout_prediction, gold_plan))

    denominator = len(test_cases) or 1
    scenes = {_cue_label(case, "scene_state") for case in all_cases if _cue_label(case, "scene_state")}
    roles = {_cue_label(case, "speaker_role") for case in all_cases if _cue_label(case, "speaker_role")}
    texts = {str(case.get("target_text", "")).strip() for case in all_cases if str(case.get("target_text", "")).strip()}
    keys = {_source_key(case) for case in all_cases if any(_source_key(case))}
    all_grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for case in all_cases:
        all_grouped[_source_key(case)].add(_plan_signature(dict(case.get("gold_plan", {}))))
    source_key_plan_counts = [len(signatures) for signatures in all_grouped.values()]
    deterministic_source_keys = sum(1 for count in source_key_plan_counts if count == 1)
    source_key_count = len(all_grouped)
    taxonomy_valid, taxonomy_invalid, taxonomy_valid_fraction = _prompt_taxonomy_coverage(all_cases)

    return {
        "scope": "controlled_source_label_diagnostic",
        "broad_benchmark_ready": False,
        "total_cases": len(all_cases),
        "public_context_audio_rows": sum(1 for case in all_cases if bool(case.get("context_audio"))),
        "unique_target_texts": len(texts),
        "unique_role_labels": len(roles),
        "unique_scene_labels": len(scenes),
        "unique_emotion_intensity_keys": len(keys),
        "deterministic_source_key_mappings": deterministic_source_keys,
        "ambiguous_source_key_mappings": sum(1 for count in source_key_plan_counts if count > 1),
        "source_key_mapping_count": source_key_count,
        "deterministic_source_key_fraction": deterministic_source_keys / (source_key_count or 1),
        "max_plans_per_source_key": max(source_key_plan_counts, default=0),
        "prompt_taxonomy_valid_gold_plans": taxonomy_valid,
        "prompt_taxonomy_invalid_gold_plans": taxonomy_invalid,
        "prompt_taxonomy_valid_fraction": taxonomy_valid_fraction,
        "train_lookup_keys": len(lookup),
        "ambiguous_train_keys": sum(1 for counter in grouped.values() if len(counter) > 1),
        "test_cases": len(test_cases),
        "test_keys_seen_in_train": seen_keys,
        "lookup_exact_plan_accuracy": exact_matches / denominator,
        "lookup_plan_slot_accuracy": mean(slot_scores) if slot_scores else 0.0,
        "leave_key_out_test_cases": len(test_cases),
        "leave_key_out_heldout_keys": len(heldout_keys),
        "leave_key_out_exact_plan_accuracy": key_holdout_exact_matches / denominator,
        "leave_key_out_plan_slot_accuracy": mean(key_holdout_slot_scores) if key_holdout_slot_scores else 0.0,
        "prior_only_field": "source_emotion",
        "prior_only_train_keys": len(prior_lookup),
        "prior_only_ambiguous_train_keys": sum(1 for counter in prior_grouped.values() if len(counter) > 1),
        "prior_only_test_keys_seen_in_train": prior_seen_keys,
        "prior_only_exact_plan_accuracy": prior_exact_matches / denominator,
        "prior_only_plan_slot_accuracy": mean(prior_slot_scores) if prior_slot_scores else 0.0,
        "prior_only_counterfactual_edits": len(prior_cf_consistency_scores),
        "prior_only_counterfactual_expected_change_accuracy": mean(prior_cf_expected_scores) if prior_cf_expected_scores else 0.0,
        "prior_only_counterfactual_unexpected_change_rate": mean(prior_cf_unexpected_scores) if prior_cf_unexpected_scores else 0.0,
        "prior_only_counterfactual_consistency_score": mean(prior_cf_consistency_scores) if prior_cf_consistency_scores else 0.0,
        "plan_fields": list(PLAN_FIELDS) + ["emphasis"],
    }


def summarize_source_key_holdout_prior(root: Path) -> dict[str, object]:
    split_root = root / "data/benchmark/source_label/source_key_holdout/splits"
    train_cases = read_jsonl(split_root / "train_cases_public.jsonl")
    test_cases = read_jsonl(split_root / "test_cases_public.jsonl")
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for case in train_cases:
        emotion = _source_key(case)[0]
        if emotion:
            grouped[emotion][_plan_signature(dict(case.get("gold_plan", {})))] += 1
    lookup = {
        emotion: dict(json.loads(sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]))
        for emotion, counter in grouped.items()
    }
    fallback = _majority_plan(train_cases)
    exact_matches = 0
    seen_keys = 0
    slot_scores: list[float] = []
    cf_expected_scores: list[float] = []
    cf_unexpected_scores: list[float] = []
    cf_consistency_scores: list[float] = []
    for case in test_cases:
        emotion = _source_key(case)[0]
        if emotion in lookup:
            seen_keys += 1
        prediction = lookup.get(emotion, fallback)
        gold_plan = dict(case.get("gold_plan", {}))
        exact_matches += int(_plan_signature(prediction) == _plan_signature(gold_plan))
        slot_scores.append(plan_slot_accuracy(prediction, gold_plan))
        for counterfactual in case.get("counterfactuals", []):
            if not isinstance(counterfactual, dict):
                continue
            expected_delta = counterfactual.get("expected_plan_delta", {})
            if not isinstance(expected_delta, dict):
                continue
            counterfactual_emotion = normalize_label(expected_delta.get("emotion", emotion))
            counterfactual_prediction = lookup.get(counterfactual_emotion, fallback)
            expected_score, unexpected_rate, consistency = _counterfactual_score(prediction, counterfactual_prediction, expected_delta)
            cf_expected_scores.append(expected_score)
            cf_unexpected_scores.append(unexpected_rate)
            cf_consistency_scores.append(consistency)
    denominator = len(test_cases) or 1
    return {
        "baseline_id": "source_key_holdout_source_emotion_prior_only",
        "scope": "source_key_disjoint_split_diagnostic",
        "prior_field": "source_emotion",
        "train_cases": len(train_cases),
        "test_cases": len(test_cases),
        "train_prior_keys": len(lookup),
        "ambiguous_prior_keys": sum(1 for counter in grouped.values() if len(counter) > 1),
        "test_keys_seen_in_train": seen_keys,
        "key_coverage": seen_keys / denominator,
        "exact_plan_accuracy": exact_matches / denominator,
        "plan_slot_accuracy": mean(slot_scores) if slot_scores else 0.0,
        "citation_required_grounded_score": 0.0,
        "counterfactual_edits": len(cf_consistency_scores),
        "counterfactual_expected_change_accuracy": mean(cf_expected_scores) if cf_expected_scores else 0.0,
        "counterfactual_unexpected_change_rate": mean(cf_unexpected_scores) if cf_unexpected_scores else 0.0,
        "counterfactual_consistency_score": mean(cf_consistency_scores) if cf_consistency_scores else 0.0,
        "claim_use": "diagnostic only; no case record or citations",
    }
