# VoxReason Source-Label Files

This directory contains the released source-label split used by the public VoxReason package.

## What Is Here

- `summary.json`: split counts, source-license note, and claim scope.
- `checksums.sha256`: SHA-256 checksums for the released benchmark files.
- `splits/train_cases_public.jsonl`: 67 training cases.
- `splits/dev_cases_public.jsonl`: 17 development cases.
- `splits/test_cases_public.jsonl`: 16 test cases.
- `train_*_sft.jsonl`: supervised planner examples for evidence-grounded and transcript-only modes.
- `dev_*_prompts.jsonl` and `test_*_prompts.jsonl`: inference prompts.
- `dev_gold_predictions.jsonl` and `test_gold_predictions.jsonl`: gold planner outputs for scoring.
- `train_grounding_preferences.jsonl`: preference-pair data derived from automatic evidence and plan checks.
- `source_key_holdout/`: a source-key-disjoint split and prompt files for anti-shortcut checks.

## Scope

The files contain derived labels, text prompts, cue spans, metadata, and expected speaking plans. They do not include raw audio. If your workflow needs waveforms, obtain them from the original RAVDESS release and follow its license terms.

## Quick Checks

```bash
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/build_source_key_holdout_split.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
```

These checks validate file structure, confirm checksums, rebuild prompts, and verify that the released test gold outputs still score cleanly under the public verifier.
