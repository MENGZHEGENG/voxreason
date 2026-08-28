# VoxReason

VoxReason is a public code and paper package for evidence-grounded speech reasoning. The project focuses on listener-free process supervision: the model cites dialogue and speech cues, predicts a structured speaking plan, and is evaluated with automatic checks before any future listener study.

## What This Release Contains

- `paper/main.tex`: venue-neutral manuscript source.
- `scripts/draw_figures.py`: generates the paper TikZ figure sources.
- `scripts/reproduce_results.py`: regenerates the paper tables and public summary from compact result inputs.
- `src/voxreason_public/`: small readers and aggregators for the public result files.
- `data/results/`: compact public result inputs used to rebuild the paper tables.
- `tests/`: reproducibility and public-hygiene checks.

This repository intentionally excludes generated tables, generated figures, site-specific launch files, machine-local paths, model weights, raw audio, and raw model completions.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e . pytest
python3 scripts/reproduce_results.py
python3 scripts/draw_figures.py
python3 -m pytest
```

The generated files are intentionally ignored by Git:

- `paper/tables/*.tex`
- `paper/figures/*.tex`
- `data/results/public_summary.json`

## Build The Paper

Use a standard LaTeX installation from the repository root:

```bash
cd paper
latexmk -pdf main.tex
```

If `latexmk` is unavailable, run `pdflatex`, `bibtex`, `pdflatex`, `pdflatex` on `main.tex` from the `paper` directory.

## Claim Boundary

The current evidence supports automatic, listener-free process claims: evidence precision/recall/F1, plan-slot accuracy, grounded score, hallucinated-evidence rate, counterfactual cue consistency, and lightweight acoustic preflight checks. It does not report listener judgments or generated-audio user ratings.

## Main Reproduction Commands

```bash
python3 scripts/reproduce_results.py
python3 scripts/draw_figures.py
python3 -m pytest
```

Expected table highlights:

| Setting | Evidence F1 | Plan acc. | Grounded | Halluc. rate |
| --- | ---: | ---: | ---: | ---: |
| Text-only control | 0.857 | 0.185 | 0.569 | 0.000 |
| Evidence-grounded planner | 1.000 | 1.000 | 1.000 | 0.000 |
| Qwen2.5-3B SFT | 1.000 | 0.811 | 0.915 | 0.000 |
| Qwen2.5-7B SFT | 1.000 | 0.725 | 0.876 | 0.000 |
| Qwen2.5-7B preference | 1.000 | 0.689 | 0.860 | 0.000 |

## Citation

If this code helps your work, cite the paper draft in `paper/main.tex`.
