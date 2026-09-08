# VoxReason

VoxReason is a public benchmark and verifier package for listener-free evaluation of source-grounded speech planning. It asks one controlled question: with the utterance fixed and the licensed cue changed, does a planner cite the right source record, choose the licensed delivery fields, and update only the linked fields?

This public repository packages the VoxReason source-label split, verifier, prompt builders, holdout builders, compact reproduction scripts, and public-hygiene checks needed to verify the paper's planning-stage claims without raw audio, private checkpoints, or site-local launch files.

## Start Here

- Read `BENCHMARK.md` for benchmark scope, reporting rules, and claim boundaries.
- Run `Fast Verification` if you want to confirm the public release before scoring new outputs.
- Use `scripts/score_predictions.py` if you already have planner outputs for the released splits.
- Cite the preprint with the BibTeX block in `Citation` or the repository-level `CITATION.cff`.

## What You Can Check

- Whether a planner cites permitted source evidence.
- Whether the predicted speaking-plan fields match the licensed delivery labels.
- Whether a one-cue edit moves the linked fields while leaving unrelated fields fixed.
- Whether the released split, prompt builders, and compact summaries reproduce cleanly.

## Fast Verification

For a quick independent check after installation, run:

```bash
python3 scripts/check_benchmark_files.py
python3 scripts/reproduce_results.py
python3 -m pytest tests/test_reproduce_results.py tests/test_public_hygiene.py
```

These commands verify file integrity, rebuild the compact public summaries, and check that the public-facing text stays within the listener-free source-label scope.

## Choose A Path

- Validate the released data and prompt builders first, start with `scripts/validate_benchmark_data.py`, `scripts/check_benchmark_files.py`, and the holdout builders.
- Score your own planner outputs, use `scripts/score_predictions.py` on the matching split.
- Rebuild the compact public result summaries, run `scripts/reproduce_results.py`.
- Understand what the package supports and what it does not, read `Claim Boundary` here and the fuller benchmark card in `BENCHMARK.md`.

## Repository Map

- `BENCHMARK.md` explains benchmark scope, splits, metrics, and reporting rules.
- `CITATION.cff` mirrors the preprint citation for GitHub's citation UI.
- `data/benchmark/source_label/` stores the public source-label cases, prompts, and gold planner outputs.
- `scripts/check_benchmark_files.py` verifies checksums and required file structure.
- `scripts/validate_benchmark_data.py` validates the released JSONL files.
- `scripts/build_benchmark_prompts.py` regenerates planner prompts from the released cases.
- `scripts/build_source_key_holdout_split.py` rebuilds the source-key-disjoint anti-shortcut split.
- `scripts/build_source_emotion_holdout_split.py` rebuilds the source-emotion-disjoint anti-shortcut split.
- `scripts/score_predictions.py` scores predictions against the released benchmark files.
- `scripts/reproduce_results.py` rebuilds the compact public score summaries.
- `src/voxreason_public/` contains small readers and helpers used by the public scripts.
- `data/results/` contains the compact result inputs used by the reproduction scripts.
- `tests/` contains reproducibility and public-hygiene checks.

## Claim Boundary

VoxReason evaluates whether a planner grounds each delivery decision in permitted source evidence before synthesis.

- Supported here: evidence precision/recall/F1, decisive-cue recall, plan-slot accuracy, citation-required grounded score, ungated grounded score, hallucinated-evidence rate, uncited-evidence rate, counterfactual cue consistency, lightweight acoustic preflight checks, and source-label acoustic anchors.
- Not supported here: listener judgments, rendered-speech quality claims, or broad waveform benchmarking.
- Not released here: raw licensed audio, model weights, machine-local paths, or site-specific launch details.

## Common Misreads

- This is not a speech-quality leaderboard. The package checks planning-stage grounding before synthesis.
- The bundled learned-run summaries are scorer-consistency checks, not a substitute for your own complete comparison runs.
- A high plan-slot accuracy alone does not establish source use; lead with a citation-aware metric when you report results.
- The repository is a compact public verifier package for the released split, not a release of licensed audio or private training state.

## Who This Release Serves

- Researchers who want a compact, reproducible check for source-grounded planning before any waveform study.
- Authors who need a citation-aware verifier and released splits for planning-stage ablations or anti-shortcut controls.
- Reviewers or readers who want to verify what the public package supports without reconstructing the private training setup.
- Teams who want a focused debugging target for planner outputs before they invest in listener studies or speech-quality evaluation.

## What This Release Gives You

- A compact public source-label split with prompts, gold outputs, and anti-shortcut holdout variants.
- A verifier path that checks citations, plan fields, and one-cue counterfactual locality.
- Reproduction scripts for file checks, prompt rebuilding, score summaries, and public hygiene tests.
- Compact released score summaries that help you confirm the public package is wired correctly before you run larger comparisons.

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

Generated outputs remain ignored by Git:

- `outputs/`
- `data/results/public_summary.json`
- `data/results/source_label_construct_validity.json`
- `data/results/source_label_acoustic_anchor.json`

## Key Released Numbers

Expected deterministic score highlights from the bundled benchmark files:

- Text-only control: evidence F1 `0.857`, decisive-cue recall `0.000`, plan accuracy `0.185`, citation-required score `0.427`, hallucinated-evidence rate `0.000`.
- Source-label upper bound: evidence F1 `1.000`, decisive-cue recall `1.000`, plan accuracy `1.000`, citation-required score `1.000`, hallucinated-evidence rate `0.000`.

For source-label measurement examples, uncited-evidence rate is `0.250` for the text-only control and `0.000` for the source-label upper bound.

The released source-label split is intentionally focused. `scripts/reproduce_results.py` writes `data/results/source_label_construct_validity.json`, which reports zero public context-audio entries, two target utterances, one scene label, `15/15` deterministic source emotion/intensity mappings, and `100/100` gold plans covered by the prompt taxonomy. It also writes `data/results/source_key_holdout_prior_only.json`, which shows why prior-only shortcuts are unsafe under the source-key-disjoint split.

Bundled learned-run summaries are provided only as scorer-consistency checks:

- Qwen2.5-3B source-labelled SFT: evidence F1 `1.000`, plan accuracy `0.811`, citation-required score `0.915`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B source-labelled SFT: evidence F1 `1.000`, plan accuracy `0.725`, citation-required score `0.876`, hallucinated-evidence rate `0.000`.
- Qwen2.5-7B preference: evidence F1 `1.000`, plan accuracy `0.689`, citation-required score `0.860`, hallucinated-evidence rate `0.000`.

If you need manuscript-grade model comparisons, rebuild aggregates from your own complete run directory.

## Before You Compare Models

- Treat the bundled learned-run summaries as scorer-consistency checks, not as a final ranking.
- Rebuild aggregates from your own complete run directory before quoting comparison numbers in a manuscript or benchmark table.
- Name the split, the evidence condition, and the citation-aware metric whenever you report a gain.
- Keep claims at the planning stage unless you pair this package with a separate waveform or listener study.

## If You Cite VoxReason

- Cite the preprint in `Citation` or the repository-level `CITATION.cff`; treat the repository URL as a reproducibility pointer, not the primary scholarly reference.
- In papers or slides, name the split, evidence condition, and citation-aware metric alongside any reported gain.
- If you quote model comparisons, say whether they come from the compact public package or a larger private run directory.
- Do not turn planning-stage gains into claims about rendered-speech quality or listener preference without a separate study.

## Citation

If you use VoxReason, please cite the preprint below. The same metadata is mirrored in `CITATION.cff` for GitHub's citation UI. Treat the repository URL as a reproducibility pointer, not the primary scholarly citation.

- arXiv: [arXiv:2609.03203](https://arxiv.org/abs/2609.03203)

```bibtex
@article{geng2026voxreason,
  title={VoxReason: Listener-Free Evaluation of Source-Grounded Speech Planning Before Synthesis},
  author={Geng, Mengzhe},
  journal={arXiv preprint arXiv:2609.03203},
  year={2026},
  eprint={2609.03203},
  archivePrefix={arXiv},
  primaryClass={cs.SD},
  url={https://arxiv.org/abs/2609.03203}
}
```
