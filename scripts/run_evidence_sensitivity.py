#!/usr/bin/env python3
"""Run the deterministic paired evidence-sensitivity experiment.

The public VoxReason bundle contains source-label metadata and derived plans,
but no context waveforms.  This harness therefore evaluates planner behavior
on the source-key holdout and keeps the acoustic/privacy boundary explicit.
Each output row is one original/counterfactual pair for one condition and
seed.  Missing or invalid rows remain in the ledger and never enter a metric
denominator.
"""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys
from statistics import mean
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voxreason_public.benchmark import (  # noqa: E402
    ALL_PLAN_FIELDS,
    PLAN_FIELDS,
    gold_prediction,
    load_split_cases,
    normalize_label,
    score_prediction,
    write_jsonl,
)
from voxreason_public.results import _counterfactual_score  # noqa: E402


DEFAULT_CONDITIONS = (
    "prior_only",
    "source_label_oracle",
    "text_evidence_only",
    "text_evidence_counterfactual",
    "citation_echo_control",
    "shuffled_delta",
)
DEFAULT_SEEDS = (0, 1, 2)
ORDINARY_METRICS = (
    "evidence_f1",
    "decisive_cue_recall",
    "plan_slot_accuracy",
    "grounded_score",
    "citation_required_grounded_score",
    "hallucinated_evidence_rate",
    "uncited_evidence_rate",
)
PAIR_METRICS = (
    "required_change_accuracy",
    "preservation_rate",
    "unexpected_change_rate",
    "consistency_score",
)
PAIR_METRIC_SECTIONS = {
    "required_change_accuracy": "required_change_metrics",
    "preservation_rate": "preservation_metrics",
    "unexpected_change_rate": "preservation_metrics",
    "consistency_score": "preservation_metrics",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def source_group(case: dict[str, Any]) -> str:
    metadata = case.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    emotion = normalize_label(metadata.get("source_emotion", ""))
    intensity = normalize_label(metadata.get("source_intensity", ""))
    return f"{emotion}:{intensity}"


def _plan_value(plan: dict[str, Any], field: str) -> Any:
    return plan.get(field, []) if field == "emphasis" else plan.get(field, "")


def _set_plan_value(plan: dict[str, Any], field: str, value: Any) -> None:
    plan[field] = copy.deepcopy(value)


def apply_delta(plan: dict[str, Any], expected_delta: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(plan)
    for field, value in expected_delta.items():
        if field not in ALL_PLAN_FIELDS:
            raise ValueError(f"unknown plan field in expected delta: {field}")
        _set_plan_value(result, field, value)
    return result


def build_counterfactual_case(case: dict[str, Any], edit: dict[str, Any]) -> dict[str, Any]:
    """Materialize the public counterfactual as a scorer-compatible case."""
    expected_delta = edit.get("expected_plan_delta", {})
    if not isinstance(expected_delta, dict) or not expected_delta:
        raise ValueError(f"counterfactual for {case.get('case_id')} has no expected_plan_delta")
    original_id = str(case["case_id"])
    edit_id = str(edit.get("edit_id") or edit.get("edit_id", "")).strip()
    if not edit_id:
        edit_id = f"{original_id}:edit"
    result = copy.deepcopy(case)
    result["case_id"] = f"{original_id}:{edit_id}:cf"
    result["gold_plan"] = apply_delta(dict(case.get("gold_plan", {})), expected_delta)
    metadata = result.get("metadata", {})
    if isinstance(metadata, dict):
        if "emotion" in expected_delta:
            metadata["source_emotion"] = expected_delta["emotion"]
        if "energy" in expected_delta:
            metadata["source_intensity"] = "normal" if normalize_label(expected_delta["energy"]) == "medium" else metadata.get("source_intensity", "")
    changed_cue_id = str(edit.get("changed_cue_id", "")).strip()
    if changed_cue_id:
        for cue in result.get("gold_cues", []):
            if not isinstance(cue, dict) or str(cue.get("cue_id", "")) != changed_cue_id:
                continue
            cue_type = normalize_label(cue.get("cue_type", ""))
            if cue_type == "emotion" and "emotion" in expected_delta:
                cue["label"] = expected_delta["emotion"]
                cue["text"] = f"Counterfactual source metadata labels the utterance as {expected_delta['emotion']}."
            elif cue_type in {"prosody_energy", "intensity"} and "energy" in expected_delta:
                cue["label"] = expected_delta["energy"]
            break
    result["counterfactuals"] = [copy.deepcopy(edit)]
    return result


def build_pairs(cases: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id", "")).strip()
        if not case_id:
            raise ValueError("pair source case is missing case_id")
        edits = case.get("counterfactuals", [])
        if not isinstance(edits, list) or not edits:
            raise ValueError(f"case {case_id} has no counterfactual pair")
        for edit in edits:
            if not isinstance(edit, dict):
                raise ValueError(f"case {case_id} has a non-object counterfactual")
            edit_id = str(edit.get("edit_id") or edit.get("edit_id", "")).strip()
            if not edit_id:
                edit_id = f"{case_id}:edit"
            pair_id = f"{case_id}:{edit_id}"
            if pair_id in seen:
                raise ValueError(f"duplicate pair_id: {pair_id}")
            seen.add(pair_id)
            expected_delta = edit.get("expected_plan_delta", {})
            if not isinstance(expected_delta, dict) or not expected_delta:
                raise ValueError(f"pair {pair_id} has no expected plan delta")
            counterfactual = build_counterfactual_case(case, edit)
            pairs.append(
                {
                    "pair_id": pair_id,
                    "case_id": case_id,
                    "original_case_id": case_id,
                    "counterfactual_case_id": counterfactual["case_id"],
                    "source_group": source_group(case),
                    "expected_plan_delta": copy.deepcopy(expected_delta),
                    "edit_id": edit_id,
                    "original_case": case,
                    "counterfactual_case": counterfactual,
                }
            )
    return pairs


def _plan_signature(plan: dict[str, Any]) -> str:
    return json.dumps(plan, ensure_ascii=False, sort_keys=True)


def _majority_plan(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    signatures = Counter(_plan_signature(dict(case.get("gold_plan", {}))) for case in cases)
    if not signatures:
        return {}
    return dict(json.loads(sorted(signatures.items(), key=lambda item: (-item[1], item[0]))[0][0]))


def _lookup_plan(cases: Iterable[dict[str, Any]], key_fn) -> dict[Any, dict[str, Any]]:
    grouped: dict[Any, Counter[str]] = defaultdict(Counter)
    for case in cases:
        key = key_fn(case)
        grouped[key][_plan_signature(dict(case.get("gold_plan", {})))] += 1
    return {
        key: dict(json.loads(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]))
        for key, counts in grouped.items()
    }


def _emotion_key(case: dict[str, Any]) -> str:
    metadata = case.get("metadata", {})
    metadata = metadata if isinstance(metadata, dict) else {}
    return normalize_label(metadata.get("source_emotion", ""))


def _text_key(case: dict[str, Any]) -> tuple[str, str]:
    return (str(case.get("target_text", "")).strip(), str(case.get("role_profile", "")).strip())


def _text_cues(case: dict[str, Any]) -> list[dict[str, Any]]:
    allowed_sources = {"context_text", "target_text", "role_profile"}
    return [copy.deepcopy(cue) for cue in case.get("gold_cues", []) if isinstance(cue, dict) and cue.get("source") in allowed_sources]


def _citation_echo_cues(case: dict[str, Any]) -> list[dict[str, Any]]:
    cues = _text_cues(case)
    if not cues:
        return []
    cue = cues[0]
    cue["cue_id"] = f"citation_echo:{case['case_id']}"
    cue["text"] = f"Citation: {cue.get('text', '')}"
    return [cue]


def make_prediction(
    case: dict[str, Any],
    condition: str,
    *,
    seed: int,
    train_cases: list[dict[str, Any]],
    counterfactual: bool = False,
    expected_delta: dict[str, Any] | None = None,
    shuffled_delta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one deterministic prediction for a declared condition."""
    fallback = _majority_plan(train_cases)
    if condition == "source_label_oracle":
        return gold_prediction(case)

    emotion_lookup = _lookup_plan(train_cases, _emotion_key)
    text_lookup = _lookup_plan(train_cases, _text_key)
    if condition == "prior_only":
        plan = copy.deepcopy(emotion_lookup.get(_emotion_key(case), fallback))
        cited_cues: list[dict[str, Any]] = []
    elif condition in {"text_evidence_only", "text_evidence_counterfactual", "citation_echo_control"}:
        plan = copy.deepcopy(text_lookup.get(_text_key(case), fallback))
        cited_cues = _text_cues(case) if condition == "text_evidence_only" else []
        if condition == "citation_echo_control":
            cited_cues = _citation_echo_cues(case)
        if condition == "text_evidence_counterfactual" and counterfactual:
            plan = apply_delta(plan, expected_delta or {})
    elif condition == "shuffled_delta":
        plan = copy.deepcopy(fallback)
        cited_cues = []
        if counterfactual:
            plan = apply_delta(plan, shuffled_delta or expected_delta or {})
    else:
        raise ValueError(f"unknown condition: {condition}")

    return {
        "case_id": case["case_id"],
        "cited_cues": cited_cues,
        "plan": plan,
        "rationale": condition,
        "seed": seed,
    }


def _case_hash(cases: Iterable[dict[str, Any]]) -> str:
    payload = "\n".join(json.dumps(case, ensure_ascii=False, sort_keys=True) for case in cases).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    split_id: str,
    cases: list[dict[str, Any]],
    conditions: Iterable[str],
    seeds: Iterable[int],
) -> dict[str, Any]:
    pairs = build_pairs(cases)
    condition_names = list(conditions)
    seed_list = [int(seed) for seed in seeds]
    required_slots = sum(len(pair["expected_plan_delta"]) for pair in pairs)
    preserved_slots = sum(len(set(ALL_PLAN_FIELDS) - set(pair["expected_plan_delta"])) for pair in pairs)
    case_ids = [str(case["case_id"]) for case in cases]
    groups = {str(case["case_id"]): source_group(case) for case in cases}
    pair_ids = [pair["pair_id"] for pair in pairs]
    conditions_payload: dict[str, Any] = {}
    for condition in condition_names:
        conditions_payload[condition] = {
            "split": split_id,
            "case_ids": case_ids,
            "pair_ids": pair_ids,
            "seeds": seed_list,
            "input_fields": ["context_text", "target_text", "role_profile", "context_audio", "gold_cues"],
            "output_fields": ["cited_cues", "plan"],
            "metric_denominators": {
                "cases": len(case_ids),
                "pairs": len(pair_ids),
                "required_slots": required_slots,
                "preserved_slots": preserved_slots,
            },
            "missing_policy": "report_and_exclude_from_ranking",
            "entry_point": "scripts/run_evidence_sensitivity.py",
        }
    return {
        "schema_version": "voxreason_evidence_sensitivity_v1",
        "split_id": split_id,
        "case_ids": case_ids,
        "pair_ids": pair_ids,
        "pairs": [
            {
                "pair_id": pair["pair_id"],
                "original_case_id": pair["original_case_id"],
                "counterfactual_case_id": pair["counterfactual_case_id"],
                "source_group": pair["source_group"],
                "expected_plan_delta": copy.deepcopy(pair["expected_plan_delta"]),
            }
            for pair in pairs
        ],
        "case_groups": groups,
        "case_hash_sha256": _case_hash(cases),
        "conditions": conditions_payload,
        "seeds": seed_list,
        "bootstrap": {"unit": "source_group", "samples": 10000, "seed": 20260911},
        "claim_boundary": "Automatic paired planner measurement on the public source-label holdout; no listener ratings and no public context audio.",
    }


def _valid_record(record: dict[str, Any]) -> bool:
    return (
        record.get("prediction_status") == "complete"
        and isinstance(record.get("original_prediction"), dict)
        and isinstance(record.get("counterfactual_prediction"), dict)
        and isinstance(record.get("required_change_metrics"), dict)
        and record["required_change_metrics"].get("status") == "ok"
    )


def _mean_metrics(records: list[dict[str, Any]], section: str, *, side: str | None = None) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for record in records:
        payload: Any = record.get(section, {})
        if side is not None:
            payload = payload.get(side, {}) if isinstance(payload, dict) else {}
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if isinstance(value, (int, float)):
                values[key].append(float(value))
    return {key: mean(items) for key, items in sorted(values.items()) if items}


def _group_bootstrap(records: list[dict[str, Any]], value_fn, *, samples: int, seed: int) -> dict[str, float]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[str(record["source_group"])].append(record)
    if not groups:
        return {"lower": 0.0, "mean": 0.0, "upper": 0.0}
    group_rows = list(groups.values())
    point_values = [value_fn(record) for record in records]
    point = mean(point_values) if point_values else 0.0
    if len(group_rows) == 1:
        return {"lower": point, "mean": point, "upper": point}
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(max(1, samples)):
        sampled = [group_rows[rng.randrange(len(group_rows))] for _ in group_rows]
        flat = [record for group in sampled for record in group]
        values = [value_fn(record) for record in flat]
        estimates.append(mean(values) if values else 0.0)
    estimates.sort()
    low_index = int(0.025 * (len(estimates) - 1))
    high_index = int(0.975 * (len(estimates) - 1))
    return {"lower": estimates[low_index], "mean": point, "upper": estimates[high_index]}


def summarize_records(
    records: Iterable[dict[str, Any]],
    *,
    bootstrap_samples: int = 10000,
    bootstrap_seed: int = 20260911,
) -> dict[str, Any]:
    record_list = list(records)
    by_condition_seed: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for record in record_list:
        by_condition_seed[str(record.get("condition", ""))][str(record.get("seed", ""))].append(record)
    result: dict[str, Any] = {
        "schema_version": "voxreason_evidence_sensitivity_summary_v1",
        "record_count": len(record_list),
        "bootstrap": {"unit": "source_group", "samples": bootstrap_samples, "seed": bootstrap_seed},
        "conditions": {},
    }
    for condition in sorted(by_condition_seed):
        condition_rows: dict[str, Any] = {"seeds": {}}
        for seed_text in sorted(by_condition_seed[condition], key=lambda value: int(value) if value.lstrip("-").isdigit() else value):
            rows = by_condition_seed[condition][seed_text]
            valid = [row for row in rows if _valid_record(row)]
            statuses = Counter("valid" if row in valid else ("missing" if row.get("prediction_status") in {"missing", "complete"} else "invalid") for row in rows)
            required = _mean_metrics(valid, "required_change_metrics")
            preservation = _mean_metrics(valid, "preservation_metrics")
            original = _mean_metrics(valid, "ordinary_metrics", side="original")
            counterfactual = _mean_metrics(valid, "ordinary_metrics", side="counterfactual")
            intervals = {
                metric: _group_bootstrap(
                    valid,
                    lambda row, metric=metric: float(
                        row[PAIR_METRIC_SECTIONS[metric]].get(metric, 0.0)
                    ),
                    samples=bootstrap_samples,
                    seed=bootstrap_seed + int(seed_text or 0) + index,
                )
                for index, metric in enumerate(PAIR_METRICS)
                if valid
            }
            condition_rows["seeds"][seed_text] = {
                "n_total": len(rows),
                "n_valid": len(valid),
                "n_missing": statuses["missing"],
                "n_invalid": statuses["invalid"],
                "status": "complete" if valid and len(valid) == len(rows) else ("incomplete" if rows else "zero_denominator"),
                "ordinary_metrics": {"original": original, "counterfactual": counterfactual},
                "required_change_metrics": required,
                "preservation_metrics": preservation,
                "source_groups": sorted({str(row.get("source_group", "")) for row in rows}),
                "bootstrap_intervals": intervals,
            }
        seed_rows = list(condition_rows["seeds"].values())
        condition_rows["n_total"] = sum(int(row["n_total"]) for row in seed_rows)
        condition_rows["n_valid"] = sum(int(row["n_valid"]) for row in seed_rows)
        condition_rows["n_missing"] = sum(int(row["n_missing"]) for row in seed_rows)
        condition_rows["status"] = "complete" if seed_rows and all(row["status"] == "complete" for row in seed_rows) else "incomplete"
        result["conditions"][condition] = condition_rows
    return result


def _record_for_pair(
    pair: dict[str, Any],
    condition: str,
    seed: int,
    train_cases: list[dict[str, Any]],
    *,
    shuffled_delta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    original_case = pair["original_case"]
    cf_case = pair["counterfactual_case"]
    expected_delta = pair["expected_plan_delta"]
    base = {
        "condition": condition,
        "seed": seed,
        "pair_id": pair["pair_id"],
        "case_id": pair["original_case_id"],
        "original_case_id": pair["original_case_id"],
        "counterfactual_case_id": pair["counterfactual_case_id"],
        "source_group": pair["source_group"],
        "prediction_status": "complete",
        "original_prediction": None,
        "counterfactual_prediction": None,
        "ordinary_metrics": {},
        "required_change_metrics": {},
        "preservation_metrics": {},
        "error_reason": "",
        "expected_plan_delta": copy.deepcopy(expected_delta),
        "input_delta": copy.deepcopy(shuffled_delta or expected_delta),
    }
    try:
        original_prediction = make_prediction(
            original_case, condition, seed=seed, train_cases=train_cases, expected_delta=expected_delta
        )
        cf_prediction = make_prediction(
            cf_case,
            condition,
            seed=seed,
            train_cases=train_cases,
            counterfactual=True,
            expected_delta=expected_delta,
            shuffled_delta=shuffled_delta,
        )
        if original_prediction is None or cf_prediction is None:
            base["prediction_status"] = "missing"
            base["error_reason"] = "condition returned no prediction"
            return base
        base["original_prediction"] = original_prediction
        base["counterfactual_prediction"] = cf_prediction
        base["ordinary_metrics"] = {
            "original": score_prediction(original_case, original_prediction),
            "counterfactual": score_prediction(cf_case, cf_prediction),
        }
        cf_score = _counterfactual_score(
            dict(original_prediction.get("plan", {})),
            dict(cf_prediction.get("plan", {})),
            expected_delta,
        )
        base["required_change_metrics"] = {
            "status": cf_score["status"],
            "required_change_accuracy": cf_score["required_change_accuracy"],
            "n_required_slots": cf_score["n_required_slots"],
        }
        base["preservation_metrics"] = {
            "status": cf_score["status"],
            "preservation_rate": cf_score["preservation_rate"],
            "unexpected_change_rate": cf_score["unexpected_change_rate"],
            "consistency_score": cf_score["consistency_score"],
            "n_preserved_slots": cf_score["n_preserved_slots"],
        }
        if cf_score["status"] != "ok":
            base["prediction_status"] = "invalid"
            base["error_reason"] = str(cf_score["status"])
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        base["prediction_status"] = "invalid"
        base["error_reason"] = f"{type(exc).__name__}: {exc}"
    return base


def run_experiment(
    *,
    root: Path = ROOT,
    output_dir: Path | None = None,
    split_name: str = "source_key_holdout",
    conditions: Iterable[str] = DEFAULT_CONDITIONS,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    bootstrap_samples: int = 10000,
    bootstrap_seed: int = 20260911,
) -> dict[str, Any]:
    holdout_root = root / "data/benchmark/source_label" / split_name
    train_cases = read_jsonl(holdout_root / "splits/train_cases_public.jsonl")
    dev_cases = read_jsonl(holdout_root / "splits/dev_cases_public.jsonl")
    test_cases = read_jsonl(holdout_root / "splits/test_cases_public.jsonl")
    condition_list = list(conditions)
    seed_list = [int(seed) for seed in seeds]
    unknown = set(condition_list) - set(DEFAULT_CONDITIONS)
    if unknown:
        raise ValueError(f"unknown conditions: {sorted(unknown)}")
    pairs = build_pairs(test_cases)
    manifest = build_manifest(f"{split_name}:test", test_cases, condition_list, seed_list)
    manifest["train_case_ids"] = [str(case["case_id"]) for case in train_cases]
    manifest["train_case_groups"] = {str(case["case_id"]): source_group(case) for case in train_cases}
    manifest["split_case_ids"] = {
        "train": [str(case["case_id"]) for case in train_cases],
        "dev": [str(case["case_id"]) for case in dev_cases],
        "test": [str(case["case_id"]) for case in test_cases],
    }
    manifest["split_case_groups"] = {
        split: {case_id: source_group(case) for case_id, case in ((str(c["case_id"]), c) for c in cases)}
        for split, cases in {"train": train_cases, "dev": dev_cases, "test": test_cases}.items()
    }
    manifest["bootstrap"] = {"unit": "source_group", "samples": bootstrap_samples, "seed": bootstrap_seed}
    all_deltas = [pair["expected_plan_delta"] for pair in pairs]
    records: list[dict[str, Any]] = []
    for condition in condition_list:
        for seed in seed_list:
            shuffled_deltas: list[dict[str, Any]] = list(all_deltas)
            random.Random(seed + bootstrap_seed).shuffle(shuffled_deltas)
            for pair_index, pair in enumerate(pairs):
                donor_delta = shuffled_deltas[pair_index] if condition == "shuffled_delta" else None
                records.append(_record_for_pair(pair, condition, seed, train_cases, shuffled_delta=donor_delta))
    summary = summarize_records(records, bootstrap_samples=bootstrap_samples, bootstrap_seed=bootstrap_seed)
    summary["manifest"] = {
        "split_id": manifest["split_id"],
        "case_hash_sha256": manifest["case_hash_sha256"],
        "conditions": condition_list,
        "seeds": seed_list,
    }
    summary["condition_notes"] = {
        "prior_only": "Source-emotion majority-plan prior trained on the source-key-disjoint training split.",
        "source_label_oracle": "Construction-level upper bound: original and counterfactual plans are copied from gold.",
        "text_evidence_only": "Target-text and role-profile lookup with public textual/role citations; no decisive source cue.",
        "text_evidence_counterfactual": "Controlled positive: applies the declared counterfactual delta to the text lookup plan.",
        "citation_echo_control": "Text lookup with a citation-like non-decisive cue, without the changed source cue.",
        "shuffled_delta": "Seeded delta permutation control; this fixture has identical deltas, so the shuffle is diagnostic and degenerate.",
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_jsonl(output_dir / "records.jsonl", records)
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": manifest, "records": records, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="source_key_holdout")
    parser.add_argument("--output-dir", default="runs/evidence_sensitivity")
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260911)
    parser.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    args = parser.parse_args()
    conditions = tuple(item.strip() for item in args.conditions.split(",") if item.strip())
    seeds = tuple(int(item.strip()) for item in args.seeds.split(",") if item.strip())
    result = run_experiment(
        root=ROOT,
        output_dir=ROOT / args.output_dir,
        split_name=args.split,
        conditions=conditions,
        seeds=seeds,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
    )
    compact = {
        "record_count": len(result["records"]),
        "split_id": result["manifest"]["split_id"],
        "conditions": conditions,
        "seeds": seeds,
    }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
