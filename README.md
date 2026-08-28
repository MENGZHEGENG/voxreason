# VoxReason

VoxReason is a public code and paper package for evidence-grounded speech reasoning. The included paper defines VoxReasonBench, a listener-free diagnostic benchmark for process supervision: the model cites permitted source cues, predicts a structured speaking plan, and is evaluated with automatic checks before any future listener study.

## What This Release Contains

- `paper/main.tex`: paper source describing the method and benchmark.
- `BENCHMARK.md`: benchmark card with scope, split, metric, and source-data details.
- `CITATION.cff` and `DATA_USE.md`: citation and data-use notes for the code and benchmark.
- `data/benchmark/source_label/`: VoxReasonBench public case splits, prompt files, and gold planner outputs.
- `scripts/reproduce_results.py`: rebuilds derived result files from compact result inputs.
- `scripts/build_benchmark_prompts.py`: rebuilds planner prompts from the public benchmark cases.
- `scripts/score_predictions.py`: scores model predictions against the public benchmark cases.
- `scripts/check_benchmark_files.py`: verifies benchmark checksums and public case validity.
- `src/voxreason_public/`: small readers and aggregators for the public result files.
- `data/results/`: compact public result inputs used by the reproduction scripts.
- `tests/`: reproducibility and public-hygiene checks.

This repository intentionally excludes generated tables, site-specific launch files, machine-local paths, model weights, raw audio, and raw model completions.

## Benchmark Scope

VoxReasonBench evaluates whether a speech-reasoning planner grounds each delivery decision in permitted source evidence. It is not a waveform-quality benchmark and does not report listener judgments.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e . pytest
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
python3 scripts/reproduce_results.py
python3 -m pytest
```

The generated files are intentionally ignored by Git:

- `outputs/`
- `paper/tables/*.tex`
- `data/results/public_summary.json`

## Build The Paper

Run the reproduction script before compiling, because the LaTeX tables are rebuilt locally and ignored by Git:

```bash
python3 scripts/reproduce_results.py
```

Use a standard LaTeX installation from the repository root:

```bash
cd paper
latexmk -pdf main.tex
```

If `latexmk` is unavailable, run `pdflatex`, `bibtex`, `pdflatex`, `pdflatex` on `main.tex` from the `paper` directory.

## Claim Boundary

The current evidence supports automatic, listener-free process claims: evidence precision/recall/F1, plan-slot accuracy, grounded score, hallucinated-evidence rate, counterfactual cue consistency, and lightweight acoustic preflight checks. It does not report listener judgments or waveform user ratings.

The source-label split is intentionally narrow. `scripts/reproduce_results.py` also writes `data/results/source_label_construct_validity.json`, which reports zero public context-audio rows, two target utterances, one scene label, and a source emotion/intensity lookup with test exact-plan accuracy `1.000`. Treat learned-model rows as diagnostics, not broad benchmark rankings.

## Main Reproduction Commands

```bash
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
python3 scripts/reproduce_results.py
python3 -m pytest
```

Expected score highlights:

- Text-only control: evidence F1 `0.857`, plan accuracy `0.185`, grounded score `0.569`, hallucinated-evidence rate `0.000`.
- Source-label upper bound: evidence F1 `1.000`, plan accuracy `1.000`, grounded score `1.000`, hallucinated-evidence rate `0.000`.
- Qwen2.5-3B SFT: evidence F1 `1.000`, plan accuracy `0.811`, grounded score `0.915`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B SFT: evidence F1 `1.000`, plan accuracy `0.725`, grounded score `0.876`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B preference: evidence F1 `1.000`, plan accuracy `0.689`, grounded score `0.860`, hallucinated-evidence rate `0.000`.

## Citation

If this code helps your work, cite the paper draft in `paper/main.tex` and the repository metadata in `CITATION.cff`. See `DATA_USE.md` for source-data and license notes.
