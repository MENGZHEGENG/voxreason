# VoxReason Benchmark Card

The VoxReason public benchmark is a listener-independent source-label suite for source-grounded speech planning. It asks one controlled question: with the utterance fixed, can a planner cite the source cue that licenses the speaking plan and update only the linked fields when that cue changes?

Use this benchmark when you want to test that planning-stage claim directly. Keep conclusions at the planning stage: the public package does not support waveform or listener judgments.

## Why This Benchmark Exists

Many speech systems make delivery decisions before any waveform is rendered. Those decisions can sound plausible even when they come from a shortcut. VoxReason makes that failure visible at the planning stage by checking citations, plan-slot agreement, and one-cue counterfactual locality on derived public records.

## Intended Use

Use this suite to test whether a planner follows the licensed source cue before any listener study. It supports checks for:

- evidence precision, recall, and F1
- plan-slot accuracy
- citation-required grounded score
- grounded score
- hallucinated-evidence rate
- uncited-evidence rate
- counterfactual cue consistency

Do not use this suite to claim waveform quality, listener preference, or broad deployment readiness. The released files do not contain waveforms or listener ratings.

## What This Benchmark Does Not Answer

- It does not measure synthesized-speech quality.
- It does not measure listener preference.
- It does not establish deployment readiness.
- It does test whether a planner followed the licensed source cue before synthesis.

## What You Can Report

Use this benchmark to report evidence about source-grounded planning on the released source-label split and its stricter holdout variants. Good claims stay at the planning stage: whether a system cites the right cue, chooses the licensed delivery fields, and updates only the linked fields under a controlled cue edit.

Do not treat the public package as a waveform benchmark. It does not support claims about synthesis quality, perceptual preference, or deployment readiness.

## Released Data

The public source-label split contains 100 cases:

- train: 67
- development: 17
- test: 16

Each case includes:

- a case identifier
- source information and permitted evidence cues
- transcript text
- structured speaking-plan labels
- counterfactual cue edits

The files under `data/benchmark/source_label/` also include prompt variants, gold planner outputs for development and test scoring, and training preference pairs derived from automatic evidence and plan checks.

Two stricter split variants are included for anti-shortcut checks:

- `source_key_holdout/` holds out emotion-intensity source keys across train, development, and test.
- `source_emotion_holdout/` holds out full source-emotion labels across train, development, and test. The released counts are `56/12/32`.

## Task Variants

- Evidence-grounded planning: the model receives transcript text plus permitted cue evidence and predicts citations and speaking-plan slots.
- Transcript-only control: the model receives transcript text without the cue-evidence channel.
- Counterfactual cue edit: the model receives a target-preserving cue change, and the evaluator checks whether the plan changes in the expected direction.

## Metrics

- Evidence F1: overlap between cited evidence identifiers and permitted gold evidence identifiers.
- Plan-slot accuracy: exact agreement for structured speaking-plan fields.
- Citation-required grounded score: primary combined score. It multiplies the grounded score by cited-evidence recall when required gold evidence exists.
- Grounded score: combined evidence and plan score used for source-grounding measurement.
- Hallucinated-evidence rate: fraction of cited evidence identifiers that are not permitted for the case.
- Uncited-evidence rate: fraction of required source cues omitted by the prediction.
- Counterfactual cue consistency: agreement between cue edits and predicted plan changes.

## Source Provenance

The case records are derived from RAVDESS source labels. The repository stores derived labels, cue records, text prompts, and expected speaking plans only. If you need waveform inputs, obtain them from the original RAVDESS release and follow its license terms.

## Reproducibility Checks

From the repository root, run:

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

The checksum file `data/benchmark/source_label/checksums.sha256` records the released source-label files checked by `scripts/check_benchmark_files.py`.

## Minimal Evaluation Recipe

- Validate the released files with `scripts/check_benchmark_files.py` and `scripts/validate_benchmark_data.py`.
- Score one evidence-grounded output file with `scripts/score_predictions.py` on the matching split.
- Rebuild the compact public summaries with `scripts/reproduce_results.py` before comparing your result against the bundled checks.
- Report the split, evidence condition, and citation-aware metric together; then state whether the number comes from the compact public package or your own larger run directory.

## Reporting Checklist

- Report the split you used: public source-label, `source_key_holdout/`, or `source_emotion_holdout/`.
- Report whether the model had access to cue evidence or only transcript text.
- Include citation-aware metrics, not only plan-slot accuracy.
- Treat the holdout variants as anti-shortcut checks that test whether gains survive disjoint evaluation.
- Keep claims at the planning stage unless you add a separate waveform study.

## Comparison Discipline

- Compare systems under the same split, the same evidence condition, and the same verifier settings.
- Treat bundled learned-run summaries as verifier sanity checks; rebuild manuscript-grade comparisons from your own complete run directory.
- If you report a gain, name the paired baseline and say whether the comparison changes source access, model scale, or training recipe.
- If a number comes from the compact public package, say so directly instead of implying broader model ranking coverage.

## Before You Publish Numbers

- State whether the result comes from the public source-label split or a stricter holdout.
- State whether the model saw cue evidence or transcript text only.
- Lead with a citation-aware metric, not only plan-slot accuracy.
- If you mention model comparisons, note whether the numbers come from the compact public package or a larger private run directory.
- Cite the preprint in `README.md` or the repository-level `CITATION.cff` when you use the benchmark, verifier, or reproduced score summaries; treat the repository URL as a reproducibility pointer.

## Minimal Reporting Template

Use a sentence like the following when you report a number from this package:

- On `[split]`, under `[evidence condition]`, the released verifier gave citation-required grounded score `x` for `[system]`.
- On `[split]`, removing cue evidence changed citation-required grounded score from `x` to `y` under the released planning-stage verifier.

If you compare systems, add whether the numbers come from the compact public package or a larger private run directory.

## Safe Claim Patterns

Claims stay strongest when they name the split, the evidence condition, and the citation-aware metric.

- Good: on the released source-label split, adding cue evidence improved citation-required grounded score from `x` to `y` under the released verifier.
- Good: on `source_key_holdout/`, the gain remained positive after the emotion-intensity shortcut was removed.
- Good: transcript-only and prior-style controls still recovered some plan fields, so citation-required grounded score remained the main readout.

Avoid broader wording that the package does not support. Do not turn planning-stage gains into claims about full speech-generation quality, user response, or general production performance.

## Known Limits

The suite is intentionally focused. It evaluates evidence-grounded planning behavior, not synthesized waveform quality. It uses a compact public split, so model comparisons should be reported as source-grounding evidence on this setting, not as broad claims about all speech-generation settings.

For citation details, see the BibTeX block in `README.md` or the repository-level `CITATION.cff`.
