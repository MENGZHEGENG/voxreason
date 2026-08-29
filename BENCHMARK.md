# VoxReasonBench Card

VoxReasonBench is a listener-free source-label diagnostic suite for evidence-grounded speech reasoning. It tests whether a planner can cite permitted dialogue and speech-cue evidence, predict a structured speaking plan, and respond consistently when cue evidence is edited while the target text is held fixed.

## Intended Use

Use this diagnostic suite to evaluate process supervision for speech planning before running any study with listeners. It is suitable for checking evidence precision, evidence recall, evidence F1, plan-slot accuracy, citation-required grounded score, ungated grounded score, unsupported evidence, uncited evidence, and counterfactual cue consistency.

Do not use this suite to claim waveform quality, listener preference, or production suitability. The released files do not contain waveforms or listener ratings.

## Released Data

The public split contains 100 source-label cases:

- Training split: 67 cases.
- Development split: 17 cases.
- Test split: 16 cases.

Each case contains a case identifier, source information, transcript text, permitted evidence cues, structured speaking-plan labels, and counterfactual cue edits. The files under `data/benchmark/source_label/` also include prompt variants, gold planner outputs for development and test scoring, and training preference pairs derived from automatic evidence and plan checks.

Two stricter public split variants are included for anti-shortcut checks:

- `source_key_holdout/`: holds out emotion/intensity source keys across train, development, and test.
- `source_emotion_holdout/`: holds out full source-emotion labels across train, development, and test; the released train/development/test counts are `56/12/32`.

## Task Variants

- Evidence-grounded planning: the model receives transcript text plus permitted cue evidence and predicts citations and speaking-plan slots.
- Transcript-only control: the model receives transcript text without the cue evidence channel.
- Counterfactual cue edit: the model receives a target-preserving cue change, and the evaluator checks whether the plan changes in the expected direction.

## Metrics

- Evidence F1: overlap between cited evidence identifiers and permitted gold evidence identifiers.
- Plan-slot accuracy: exact agreement for structured speaking-plan fields.
- Citation-required grounded score: primary combined score; it multiplies the grounded score by cited-evidence recall when required gold evidence exists.
- Grounded score: ungated combined evidence and plan score used for diagnostics.
- Hallucinated-evidence rate: fraction of cited evidence identifiers that are not permitted for the case.
- Uncited-evidence rate: fraction of required source cues omitted by the prediction.
- Counterfactual cue consistency: agreement between cue edits and predicted plan changes.

## Source Data

The case records are derived from RAVDESS source labels. The repository stores derived labels, cue records, text prompts, and expected speaking plans only. Users who need waveform inputs should obtain them from the original RAVDESS source and follow its license terms.

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

## Known Limits

The diagnostic suite is intentionally narrow. It evaluates evidence-grounded planning behavior, not synthesized waveform quality. It also uses a compact public split, so model comparisons should be reported as diagnostic evidence rather than broad claims about all speech-generation settings.
