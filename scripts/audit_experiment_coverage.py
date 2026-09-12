#!/usr/bin/env python3
"""Fail-closed audit for a paired VoxReason experiment ledger.

The audit treats the manifest as the denominator contract.  A result is not
complete merely because some rows contain predictions: every declared
condition, seed, and pair must have one row, and missing rows are errors.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _is_valid(record: dict[str, Any]) -> bool:
    metrics = record.get("required_change_metrics")
    return (
        record.get("prediction_status") == "complete"
        and isinstance(record.get("original_prediction"), dict)
        and isinstance(record.get("counterfactual_prediction"), dict)
        and isinstance(metrics, dict)
        and metrics.get("status") == "ok"
    )


def _numeric_means(rows: list[dict[str, Any]], section: str, side: str | None = None) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        payload: Any = row.get(section, {})
        if side is not None:
            payload = payload.get(side, {}) if isinstance(payload, dict) else {}
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values[key].append(float(value))
    return {key: mean(items) for key, items in values.items() if items}


def _compare_means(
    errors: list[str],
    label: str,
    observed: dict[str, float],
    expected: dict[str, Any],
    *,
    tolerance: float = 1e-10,
) -> None:
    if not isinstance(expected, dict):
        errors.append(f"summary {label} is not an object")
        return
    for key, value in observed.items():
        if key not in expected or not isinstance(expected[key], (int, float)):
            errors.append(f"summary {label}.{key} cannot be recomputed from ledger")
        elif abs(float(expected[key]) - value) > tolerance:
            errors.append(f"summary {label}.{key} disagrees with ledger: {expected[key]} != {value}")


def _expected_pairs(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pairs = manifest.get("pairs", [])
    result: dict[str, dict[str, Any]] = {}
    if isinstance(pairs, list):
        for pair in pairs:
            if isinstance(pair, dict) and str(pair.get("pair_id", "")).strip():
                result[str(pair["pair_id"])] = pair
    if result:
        return result
    # Backward-compatible fallback for early manifests.  The generated
    # experiment manifest includes full pair specs; this fallback still checks
    # row completeness when auditing a hand-authored manifest.
    return {str(pair_id): {"pair_id": str(pair_id)} for pair_id in manifest.get("pair_ids", [])}


def _split_errors(manifest: dict[str, Any], errors: list[str]) -> None:
    split_case_ids = manifest.get("split_case_ids", {})
    split_case_groups = manifest.get("split_case_groups", {})
    if not isinstance(split_case_ids, dict) or not isinstance(split_case_groups, dict):
        return

    case_owner: dict[str, str] = {}
    for split, case_ids in split_case_ids.items():
        if not isinstance(case_ids, list):
            errors.append(f"split_case_ids[{split}] is not a list")
            continue
        for case_id in case_ids:
            case_id = str(case_id)
            if case_id in case_owner:
                errors.append(f"case {case_id} appears in multiple splits: {case_owner[case_id]}, {split}")
            case_owner[case_id] = str(split)

    group_owner: dict[str, set[str]] = defaultdict(set)
    for split, groups in split_case_groups.items():
        if not isinstance(groups, dict):
            errors.append(f"split_case_groups[{split}] is not an object")
            continue
        for case_id, group in groups.items():
            case_id = str(case_id)
            group = str(group)
            if case_owner.get(case_id) not in {None, str(split)}:
                errors.append(f"case {case_id} has inconsistent split declarations")
            group_owner[group].add(str(split))
    for group, splits in sorted(group_owner.items()):
        if len(splits) > 1:
            errors.append(f"source group {group} crosses split boundaries: {sorted(splits)}")


def audit_experiment(
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit a manifest, paired ledger, and optional aggregate summary."""
    errors: list[str] = []
    pair_map = _expected_pairs(manifest)
    case_ids = {str(case_id) for case_id in manifest.get("case_ids", [])}
    case_groups = {str(key): str(value) for key, value in (manifest.get("case_groups", {}) or {}).items()}
    _split_errors(manifest, errors)

    conditions = manifest.get("conditions", {})
    if not isinstance(conditions, dict):
        errors.append("manifest conditions is not an object")
        conditions = {}
    expected_keys: set[tuple[str, int, str]] = set()
    for condition, payload in conditions.items():
        if not isinstance(payload, dict):
            errors.append(f"condition {condition} is not an object")
            continue
        pair_ids = [str(pair_id) for pair_id in payload.get("pair_ids", manifest.get("pair_ids", []))]
        seeds = [int(seed) for seed in payload.get("seeds", manifest.get("seeds", []))]
        for pair_id in pair_ids:
            if pair_id not in pair_map:
                errors.append(f"condition {condition} declares unknown pair_id {pair_id}")
            for seed in seeds:
                expected_keys.add((str(condition), seed, pair_id))

    observed_keys: set[tuple[str, int, str]] = set()
    rows_by_condition_seed: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    valid_count = 0
    status_counts: Counter[str] = Counter()
    for index, row in enumerate(records):
        condition = str(row.get("condition", ""))
        try:
            seed = int(row.get("seed"))
        except (TypeError, ValueError):
            errors.append(f"row {index} has invalid seed")
            continue
        pair_id = str(row.get("pair_id", "")).strip()
        key = (condition, seed, pair_id)
        if key in observed_keys:
            errors.append(f"duplicate ledger row for condition={condition}, seed={seed}, pair_id={pair_id}")
        observed_keys.add(key)
        rows_by_condition_seed[(condition, seed)].append(row)
        status = str(row.get("prediction_status", ""))
        status_counts[status] += 1
        if status in {"missing", "invalid"} and not str(row.get("error_reason", "")).strip():
            errors.append(f"row {index} marked {status} without an explicit error_reason")
        if key not in expected_keys:
            errors.append(f"unexpected ledger row for condition={condition}, seed={seed}, pair_id={pair_id}")
            continue
        pair = pair_map.get(pair_id, {})
        expected_case_id = str(pair.get("original_case_id", row.get("original_case_id", row.get("case_id", ""))))
        expected_cf_id = str(pair.get("counterfactual_case_id", row.get("counterfactual_case_id", "")))
        if case_ids and str(row.get("case_id", "")) not in case_ids:
            errors.append(f"row {index} uses case outside declared split: {row.get('case_id')}")
        if pair.get("original_case_id") and str(row.get("original_case_id")) != expected_case_id:
            errors.append(f"row {index} original_case_id does not match pair {pair_id}")
        if expected_cf_id and str(row.get("counterfactual_case_id")) != expected_cf_id:
            errors.append(f"row {index} counterfactual_case_id does not match pair {pair_id}")
        expected_group = str(pair.get("source_group", case_groups.get(expected_case_id, "")))
        if expected_group and str(row.get("source_group", "")) != expected_group:
            errors.append(f"row {index} source_group does not match pair {pair_id}")
        if _is_valid(row):
            valid_count += 1
        elif status == "complete":
            errors.append(f"row {index} is complete but lacks a valid paired prediction")

    missing_keys = sorted(expected_keys - observed_keys)
    for condition, seed, pair_id in missing_keys:
        errors.append(f"missing expected ledger row: condition={condition}, seed={seed}, pair_id={pair_id}")

    summary_checked = summary is not None
    if summary is not None:
        if summary.get("record_count") != len(records):
            errors.append(f"summary record_count disagrees with ledger: {summary.get('record_count')} != {len(records)}")
        summary_conditions = summary.get("conditions", {})
        if not isinstance(summary_conditions, dict):
            errors.append("summary conditions is not an object")
            summary_conditions = {}
        for condition, payload in conditions.items():
            expected_payload = summary_conditions.get(condition)
            if not isinstance(expected_payload, dict):
                errors.append(f"summary is missing condition {condition}")
                continue
            summary_seeds = expected_payload.get("seeds", {})
            if not isinstance(summary_seeds, dict):
                errors.append(f"summary condition {condition} seeds is not an object")
                continue
            for seed in [int(value) for value in payload.get("seeds", manifest.get("seeds", []))]:
                rows = rows_by_condition_seed.get((str(condition), seed), [])
                valid_rows = [row for row in rows if _is_valid(row)]
                seed_summary = summary_seeds.get(str(seed))
                if not isinstance(seed_summary, dict):
                    errors.append(f"summary is missing condition={condition}, seed={seed}")
                    continue
                for field, value in {
                    "n_total": len(rows),
                    "n_valid": len(valid_rows),
                    "n_missing": sum(row.get("prediction_status") == "missing" for row in rows),
                    "n_invalid": sum(row.get("prediction_status") == "invalid" for row in rows),
                }.items():
                    if seed_summary.get(field) != value:
                        errors.append(f"summary condition={condition}, seed={seed} {field} disagrees with ledger")
                _compare_means(errors, f"{condition}/{seed}/ordinary_metrics.original", _numeric_means(valid_rows, "ordinary_metrics", "original"), (seed_summary.get("ordinary_metrics") or {}).get("original", {}))
                _compare_means(errors, f"{condition}/{seed}/ordinary_metrics.counterfactual", _numeric_means(valid_rows, "ordinary_metrics", "counterfactual"), (seed_summary.get("ordinary_metrics") or {}).get("counterfactual", {}))
                _compare_means(errors, f"{condition}/{seed}/required_change_metrics", _numeric_means(valid_rows, "required_change_metrics"), seed_summary.get("required_change_metrics", {}))
                _compare_means(errors, f"{condition}/{seed}/preservation_metrics", _numeric_means(valid_rows, "preservation_metrics"), seed_summary.get("preservation_metrics", {}))

    return {
        "ok": not errors,
        "errors": errors,
        "expected_record_count": len(expected_keys),
        "observed_record_count": len(records),
        "missing_record_count": len(missing_keys),
        "valid_record_count": valid_count,
        "status_counts": dict(sorted(status_counts.items())),
        "summary_checked": summary_checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="runs/evidence_sensitivity/manifest.json")
    parser.add_argument("--records", default="runs/evidence_sensitivity/records.jsonl")
    parser.add_argument("--summary", default="runs/evidence_sensitivity/summary.json")
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    records = read_jsonl(Path(args.records))
    summary = json.loads(Path(args.summary).read_text(encoding="utf-8")) if args.summary else None
    report = audit_experiment(manifest, records, summary)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
