# VoxReason

VoxReason is a public code package for evidence-grounded speech reasoning. It includes the source-label measurement data and scripts needed to reproduce the listener-free process checks: a model cites permitted source cues, predicts a structured speaking plan, and is evaluated with automatic checks before any future listener study.

## What This Release Contains

- `BENCHMARK.md`: benchmark card with scope, split, metric, and source-data details.
- `LICENSE`: code and documentation license.
- `data/benchmark/source_label/`: VoxReasonBench public case splits, prompt files, and gold planner outputs.
- `scripts/reproduce_results.py`: rebuilds derived result files from compact result inputs.
- `scripts/build_benchmark_prompts.py`: rebuilds planner prompts from the public benchmark cases.
- `scripts/build_source_key_holdout_split.py`: rebuilds the source-key-disjoint split for anti-shortcut checks.
- `scripts/build_source_emotion_holdout_split.py`: rebuilds the source-emotion-disjoint split for stricter anti-shortcut checks.
- `scripts/score_predictions.py`: scores model predictions against the public benchmark cases.
- `scripts/check_benchmark_files.py`: verifies benchmark checksums and public case validity.
- `src/voxreason_public/`: small readers and aggregators for the public result files.
- `data/results/`: compact public result inputs used by the reproduction scripts.
- `tests/`: reproducibility and public-hygiene checks.

This repository intentionally excludes manuscript source, generated tables, figure files, site-specific launch files, machine-local paths, model weights, raw audio, and raw model completions.

## Measurement Scope

VoxReason evaluates whether a speech-reasoning planner grounds each delivery decision in permitted source evidence. The current release is a narrow source-label measurement suite, not a broad waveform-quality benchmark, and it does not report listener judgments.

## Reproducibility

This public GitHub repository is the code-and-data companion to the paper's public version. It lets an outside reader validate checksums, rebuild prompts and held-out splits, rerun the scorer, regenerate the compact public summaries, and rerun the public tests without raw audio, private checkpoints, or site-specific launch logs. For double-blind review, use the separate anonymous paper package rather than this repository URL.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e . pytest
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/build_source_key_holdout_split.py
python3 scripts/build_source_emotion_holdout_split.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
python3 scripts/reproduce_results.py
python3 -m pytest
```

The generated files are intentionally ignored by Git:

- `outputs/`
- `data/results/public_summary.json`
- `data/results/source_label_construct_validity.json`
- `data/results/source_label_acoustic_anchor.json`

## Fast Verification

For a quick independent check, run the commands below after installation:

```bash
python3 scripts/check_benchmark_files.py
python3 scripts/reproduce_results.py
python3 -m pytest tests/test_reproduce_results.py tests/test_public_hygiene.py
```

The checks verify file integrity, rebuild the compact result summaries, and confirm that public-facing text stays within the listener-free source-label scope.

## Evidence Scope

The current evidence supports automatic, listener-free process claims: evidence precision/recall/F1, decisive-cue recall, plan-slot accuracy, citation-required grounded score, ungated grounded score, hallucinated-evidence rate, uncited-evidence rate, counterfactual cue consistency, lightweight acoustic preflight checks, and source-label acoustic anchors. It does not report listener judgments or waveform user ratings.

The source-label split is intentionally narrow. `scripts/reproduce_results.py` also writes `data/results/source_label_construct_validity.json`, which reports zero public context-audio entries, two target utterances, one scene label, `15/15` deterministic source emotion/intensity mappings, and `100/100` gold plans covered by the prompt taxonomy. A source emotion/intensity lookup reaches test exact-plan accuracy `1.000`; leave-key-out exact-plan accuracy falls to `0.000` and plan-slot accuracy falls to `0.242` after same-key training cases are removed. The script also writes `data/results/source_key_holdout_prior_only.json`: on the source-key-disjoint split, a source-emotion-only prior reaches exact-plan accuracy `0.667` and plan-slot accuracy `0.958` without the case record or citations, but counterfactual consistency is `0.000`. The source-emotion holdout split has train/dev/test counts `56/12/32` with no source-emotion overlap across splits. Treat learned-model summaries as calibration measurements, not broad speech-benchmark or learned-model ordering claims.

## Main Reproduction Commands

```bash
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/build_source_key_holdout_split.py
python3 scripts/build_source_emotion_holdout_split.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
python3 scripts/reproduce_results.py
python3 -m pytest
```

Expected deterministic score highlights from bundled benchmark files:

- Text-only control: evidence F1 `0.857`, decisive-cue recall `0.000`, plan accuracy `0.185`, citation-required score `0.427`, hallucinated-evidence rate `0.000`.
- Source-label upper bound: evidence F1 `1.000`, decisive-cue recall `1.000`, plan accuracy `1.000`, citation-required score `1.000`, hallucinated-evidence rate `0.000`.

For source-label measurement examples, uncited-evidence rate is `0.250` for the text-only control and `0.000` for the source-label upper bound.

The bundled learned-run summaries are included as a lightweight consistency check for the scorer and summary writers. The source-labelled examples use source-cited prompts; they are not a substitute for rerunning the full multi-seed experiment set used by the paper. Regenerate manuscript-grade model aggregates from your own completed run directory before citing model-comparison numbers.

Bundled consistency-check learned-run summaries:

- Qwen2.5-3B source-labelled SFT: evidence F1 `1.000`, plan accuracy `0.811`, citation-required score `0.915`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B source-labelled SFT: evidence F1 `1.000`, plan accuracy `0.725`, citation-required score `0.876`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B preference: evidence F1 `1.000`, plan accuracy `0.689`, citation-required score `0.860`, hallucinated-evidence rate `0.000`.

## Citation

If this code helps your work, cite the accompanying VoxReason paper and this repository URL.
