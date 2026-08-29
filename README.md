# VoxReason

VoxReason is a public code and paper package for evidence-grounded speech reasoning. The included paper defines a listener-free source-label diagnostic suite for process supervision: the model cites permitted source cues, predicts a structured speaking plan, and is evaluated with automatic checks before any future listener study.

## What This Release Contains

- `paper/main.tex`: paper source describing the method and source-label diagnostic suite.
- `BENCHMARK.md`: benchmark card with scope, split, metric, and source-data details.
- `CITATION.cff` and `DATA_USE.md`: citation and data-use notes for the code and benchmark.
- `LICENSE`: code and documentation license; benchmark records remain subject to `DATA_USE.md`.
- `data/benchmark/source_label/`: VoxReasonBench public case splits, prompt files, and gold planner outputs.
- `scripts/reproduce_results.py`: rebuilds derived result files from compact result inputs.
- `scripts/build_anonymous_review_package.py`: creates a local anonymous review package when a venue requires anonymous materials.
- `scripts/build_benchmark_prompts.py`: rebuilds planner prompts from the public benchmark cases.
- `scripts/build_source_key_holdout_split.py`: rebuilds the source-key-disjoint split for anti-shortcut checks.
- `scripts/score_predictions.py`: scores model predictions against the public benchmark cases.
- `scripts/check_benchmark_files.py`: verifies benchmark checksums and public case validity.
- `src/voxreason_public/`: small readers and aggregators for the public result files.
- `data/results/`: compact public result inputs used by the reproduction scripts.
- `tests/`: reproducibility and public-hygiene checks.

This repository intentionally excludes generated tables, site-specific launch files, machine-local paths, model weights, raw audio, and raw model completions.

## Anonymous Review Package

This hosted repository may identify maintainers through its URL and Git history. For anonymous peer review, do not link the hosted repository directly. Build a local review package instead:

```bash
python3 scripts/build_anonymous_review_package.py
```

The package is written to `dist/voxreason-anonymous-review.zip`. It includes the tracked public files, omits Git history and regenerated outputs, and redacts the repository URL from `CITATION.cff` while keeping author metadata anonymous.

## Diagnostic Scope

VoxReason evaluates whether a speech-reasoning planner grounds each delivery decision in permitted source evidence. The current release is a narrow source-label diagnostic suite, not a broad waveform-quality benchmark, and it does not report listener judgments.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e . pytest
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/build_source_key_holdout_split.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
python3 scripts/reproduce_results.py
python3 -m pytest
```

The generated files are intentionally ignored by Git:

- `outputs/`
- `paper/tables/*.tex`
- `data/results/public_summary.json`
- `data/results/source_label_construct_validity.json`
- `data/results/source_label_acoustic_anchor.json`

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

The current evidence supports automatic, listener-free process claims: evidence precision/recall/F1, decisive-cue recall, plan-slot accuracy, citation-required grounded score, ungated grounded score, hallucinated-evidence rate, uncited-evidence rate, counterfactual cue consistency, lightweight acoustic preflight checks, and source-label acoustic anchors. It does not report listener judgments or waveform user ratings.

The source-label split is intentionally narrow. `scripts/reproduce_results.py` also writes `data/results/source_label_construct_validity.json`, which reports zero public context-audio rows, two target utterances, one scene label, `15/15` deterministic source emotion/intensity mappings, and `100/100` gold plans covered by the prompt taxonomy. A source emotion/intensity lookup reaches test exact-plan accuracy `1.000`; leave-key-out exact-plan accuracy falls to `0.000` and plan-slot accuracy falls to `0.242` after same-key training cases are removed. The script also writes `data/results/source_key_holdout_prior_only.json`: on the source-key-disjoint split, a source-emotion-only prior reaches exact-plan accuracy `0.667` and plan-slot accuracy `0.958` without the case record or citations, but counterfactual consistency is `0.000`. Treat learned-model rows as diagnostics, not broad speech-benchmark or learned-model ordering claims.

## Main Reproduction Commands

```bash
python3 scripts/validate_benchmark_data.py
python3 scripts/check_benchmark_files.py
python3 scripts/build_benchmark_prompts.py
python3 scripts/build_source_key_holdout_split.py
python3 scripts/score_predictions.py data/benchmark/source_label/test_gold_predictions.jsonl --split test
python3 scripts/reproduce_results.py
python3 -m pytest
```

Expected deterministic score highlights from bundled benchmark files:

- Text-only control: evidence F1 `0.857`, decisive-cue recall `0.000`, plan accuracy `0.185`, citation-required score `0.569`, hallucinated-evidence rate `0.000`.
- Source-label upper bound: evidence F1 `1.000`, decisive-cue recall `1.000`, plan accuracy `1.000`, citation-required score `1.000`, hallucinated-evidence rate `0.000`.

For source-label diagnostic rows, uncited-evidence rate is `0.250` for the text-only control and `0.000` for the source-label upper bound.

The bundled learned-run summaries are included as a lightweight smoke check for the scorer and table writers. They are not a substitute for rerunning the full multi-seed experiment set used by the manuscript; regenerate manuscript-grade model aggregates from your own completed run directory before citing model-comparison numbers.

Bundled smoke-check learned-run summaries:

- Qwen2.5-3B SFT: evidence F1 `1.000`, plan accuracy `0.811`, citation-required score `0.915`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B SFT: evidence F1 `1.000`, plan accuracy `0.725`, citation-required score `0.876`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B preference: evidence F1 `1.000`, plan accuracy `0.689`, citation-required score `0.860`, hallucinated-evidence rate `0.000`.

## Citation

If this code helps your work, cite the paper draft in `paper/main.tex` and the repository metadata in `CITATION.cff`. See `DATA_USE.md` for source-data and license notes.
