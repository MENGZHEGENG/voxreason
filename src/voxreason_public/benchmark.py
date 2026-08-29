from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = ROOT / "data/benchmark/source_label"
SPLIT_DIR = BENCHMARK_ROOT / "splits"
SPLITS = ("train", "dev", "test")
PLAN_FIELDS = ("emotion", "intent", "pitch", "energy", "rate", "pause", "stance")
ALL_PLAN_FIELDS = (*PLAN_FIELDS, "emphasis")

SYSTEM_PROMPT = """You are a speech-reasoning planner.
Return only valid JSON. Do not invent evidence. Produce a compact speaking plan that can condition a speech generator.
"""

PLAN_SCHEMA = {
    "cited_cues": [
        {
            "cue_id": "string",
            "cue_type": "lexical|emotion|prosody_pitch|prosody_energy|rhythm_rate|pause|overlap|speaker_role|scene_state|dialogue_act",
            "source": "context_text|context_audio|target_text|role_profile",
            "label": "string",
            "text": "short supporting span or acoustic description",
            "start_sec": "number|null",
            "end_sec": "number|null",
            "confidence": "number in [0, 1]; use 1.0 when the cue is explicitly provided",
        }
    ],
    "plan": {
        "emotion": "neutral|happy|sad|angry|afraid|tender|surprised|disgusted",
        "intent": "inform|ask|warn|reassure|apologize|persuade|tease|express-emotion",
        "pitch": "lowered|neutral|raised|variable",
        "energy": "low|medium|high",
        "rate": "slow|medium|fast",
        "pause": "none|short|long",
        "emphasis": ["word or phrase"],
        "stance": "neutral|supportive|confrontational|playful|deferential|authoritative",
    },
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_split_cases(root: Path = ROOT, split: str | None = None) -> list[dict[str, Any]]:
    split_root = root / "data/benchmark/source_label/splits"
    selected = [split] if split else list(SPLITS)
    cases: list[dict[str, Any]] = []
    for split_name in selected:
        if split_name not in SPLITS:
            raise ValueError(f"Unknown split: {split_name}")
        cases.extend(read_jsonl(split_root / f"{split_name}_cases_public.jsonl"))
    return cases


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def validate_cases(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    case_list = list(cases)
    issues: list[str] = []
    seen: set[str] = set()
    for case in case_list:
        case_id = str(case.get("case_id", ""))
        if not case_id:
            issues.append("missing case_id")
        if case_id in seen:
            issues.append(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        for key in ("context_text", "target_text", "role_profile", "gold_cues", "gold_plan", "counterfactuals", "metadata"):
            if key not in case:
                issues.append(f"{case_id}: missing {key}")
        if case.get("context_audio"):
            issues.append(f"{case_id}: context_audio must be empty in the public data")
        plan = case.get("gold_plan", {})
        for field in ALL_PLAN_FIELDS:
            if field not in plan:
                issues.append(f"{case_id}: missing plan field {field}")
        cue_ids = [cue.get("cue_id") for cue in case.get("gold_cues", [])]
        if len(cue_ids) != len(set(cue_ids)):
            issues.append(f"{case_id}: duplicate cue_id")
        for text in _walk_strings(case):
            lowered = text.lower()
            blocked_path_tokens = ("/users/", "/scr" + "atch/", "/work/" + "gengm", "private_audio", ".wav")
            if any(token in lowered for token in blocked_path_tokens):
                issues.append(f"{case_id}: non-public path string")
                break
    return {
        "case_count": len(case_list),
        "issue_count": len(issues),
        "issues": issues,
    }


def cue_brief(cue: dict[str, Any]) -> dict[str, Any]:
    return {
        "cue_id": cue["cue_id"],
        "cue_type": cue["cue_type"],
        "source": cue["source"],
        "label": cue["label"],
        "text": cue.get("text", ""),
        "confidence": cue.get("confidence", 1.0),
    }


def case_context(case: dict[str, Any], *, include_candidate_cues: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "case_id": case["case_id"],
        "context_text": case["context_text"],
        "target_text": case["target_text"],
        "role_profile": case["role_profile"],
        "context_audio": [],
    }
    if include_candidate_cues:
        payload["candidate_evidence_cues"] = [cue_brief(cue) for cue in case["gold_cues"]]
    return payload


def build_user_prompt(case: dict[str, Any], *, mode: str) -> str:
    if mode not in {"transcript_only", "evidence_grounded"}:
        raise ValueError("mode must be transcript_only or evidence_grounded")
    include_candidate_cues = mode == "evidence_grounded"
    task = (
        "Use the provided candidate evidence cues when they are relevant. Cite only cues that support the plan."
        if include_candidate_cues
        else "Use only the transcript, target text, and role profile. If audio evidence is unavailable, cite textual evidence conservatively."
    )
    return json.dumps(
        {"task": task, "input": case_context(case, include_candidate_cues=include_candidate_cues), "output_schema": PLAN_SCHEMA},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def gold_prediction(case: dict[str, Any]) -> dict[str, Any]:
    return {"case_id": case["case_id"], "cited_cues": case["gold_cues"], "plan": case["gold_plan"], "rationale": "gold"}


def build_prompt_rows(cases: Iterable[dict[str, Any]], *, mode: str, include_targets: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        row: dict[str, Any] = {
            "case_id": case["case_id"],
            "mode": mode,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(case, mode=mode)},
            ],
        }
        if include_targets:
            target = gold_prediction(case)
            row["messages"].append({"role": "assistant", "content": json.dumps(target, ensure_ascii=False, sort_keys=True)})
            row["target"] = target
        rows.append(row)
    return rows


def normalize_label(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().replace("_", "-").split())


def cue_key(cue: dict[str, Any]) -> tuple[str, str, str]:
    return (normalize_label(cue.get("cue_type")), normalize_label(cue.get("source")), normalize_label(cue.get("label")))


def cue_matches(predicted: dict[str, Any], gold: dict[str, Any]) -> bool:
    if cue_key(predicted) != cue_key(gold):
        return False
    pred_start = predicted.get("start_sec")
    pred_end = predicted.get("end_sec")
    gold_start = gold.get("start_sec")
    gold_end = gold.get("end_sec")
    if pred_start is None or pred_end is None or gold_start is None or gold_end is None:
        return True
    overlap = max(0.0, min(float(pred_end), float(gold_end)) - max(float(pred_start), float(gold_start)))
    pred_duration = max(float(pred_end) - float(pred_start), 1e-6)
    gold_duration = max(float(gold_end) - float(gold_start), 1e-6)
    return overlap / min(pred_duration, gold_duration) >= 0.5


def count_cue_matches(predicted_cues: Iterable[dict[str, Any]], gold_cues: Iterable[dict[str, Any]]) -> int:
    remaining = list(gold_cues)
    matches = 0
    for predicted in predicted_cues:
        match_index = next((idx for idx, gold in enumerate(remaining) if cue_matches(predicted, gold)), None)
        if match_index is not None:
            matches += 1
            remaining.pop(match_index)
    return matches


def plan_slot_accuracy(predicted: dict[str, Any], gold: dict[str, Any]) -> float:
    scalar_correct = sum(normalize_label(predicted.get(field)) == normalize_label(gold.get(field)) for field in PLAN_FIELDS)
    pred_emphasis = {normalize_label(item) for item in predicted.get("emphasis", [])}
    gold_emphasis = {normalize_label(item) for item in gold.get("emphasis", [])}
    emphasis_score = 1.0 if pred_emphasis == gold_emphasis else 0.0
    return (scalar_correct + emphasis_score) / (len(PLAN_FIELDS) + 1)


def score_prediction(case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, float]:
    if case["case_id"] != prediction.get("case_id"):
        raise ValueError(f"case_id mismatch: {case['case_id']!r} != {prediction.get('case_id')!r}")
    predicted_cues = list(prediction.get("cited_cues", []))
    gold_cues = list(case.get("gold_cues", []))
    matched = count_cue_matches(predicted_cues, gold_cues)
    precision = matched / len(predicted_cues) if predicted_cues else 0.0
    recall = matched / len(gold_cues) if gold_cues else 0.0
    evidence_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    hallucinated_rate = 1.0 - precision if predicted_cues else 0.0
    uncited_rate = 1.0 - recall if gold_cues else 0.0
    plan_accuracy = plan_slot_accuracy(dict(prediction.get("plan", {})), dict(case.get("gold_plan", {})))
    grounded_score = 0.45 * evidence_f1 + 0.45 * plan_accuracy + 0.10 * (1.0 - hallucinated_rate)
    return {
        "evidence_precision": precision,
        "evidence_recall": recall,
        "evidence_f1": evidence_f1,
        "plan_slot_accuracy": plan_accuracy,
        "hallucinated_evidence_rate": hallucinated_rate,
        "uncited_evidence_rate": uncited_rate,
        "grounded_score": grounded_score,
    }


def summarize_scores(scores: Iterable[dict[str, float]]) -> dict[str, float]:
    score_list = list(scores)
    metric_keys = (
        "evidence_precision",
        "evidence_recall",
        "evidence_f1",
        "plan_slot_accuracy",
        "hallucinated_evidence_rate",
        "uncited_evidence_rate",
        "grounded_score",
    )
    if not score_list:
        return {key: 0.0 for key in metric_keys}
    return {key: mean(float(score[key]) for score in score_list) for key in metric_keys}
