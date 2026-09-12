# Evidence-sensitivity analysis

## Scope

This analysis tests whether the source-grounding and counterfactual checks react to the cue that is declared as decisive. It uses the source-key-disjoint holdout defined by the public benchmark package: 60 training cases are used to fit the prior-only lookup and 24 held-out cases are evaluated. Each held-out case has one source-key counterfactual pair. The target utterance, role, scene, and non-edited fields remain fixed within a pair.

The run contains six controlled conditions, three deterministic seeds, and 24 pairs per seed and condition. The complete input matrix therefore contains 432 pair-condition-seed records. The bootstrap unit is the source group, with 10,000 resamples and seed 20260911. The coverage audit reports 432 expected records, 432 observed records, zero missing records, zero duplicates, and 432 valid records.

## Conditions

| Condition | Input available | Purpose |
| --- | --- | --- |
| Source-label oracle | Gold source record and gold plan | Construction-level upper bound for the verifier |
| Text evidence + declared delta | Text/role lookup and the declared counterfactual delta | Controlled positive showing that the locality scorer responds to the supplied delta |
| Shuffled delta | Same lookup with a seeded delta permutation | Diagnostic control; the fixture has identical deltas, so this condition is degenerate |
| Text evidence only | Text/role lookup without the decisive source cue | Tests whether non-decisive context can recover the edited cue |
| Citation echo control | A citation-like non-decisive cue without the changed source cue | Tests whether citation form alone satisfies grounding |
| Prior only | Source-emotion majority-plan prior, with no case record or citations | Anti-shortcut calibration diagnostic |

The oracle is not a learned model. The text conditions are deterministic lookup controls, and the prior-only condition is a diagnostic for the source-key split. None of these rows should be presented as a model leaderboard.

## Aggregate results

Values below are identical across the three seeds because the controls are deterministic. Metrics are averaged over the 24 held-out pairs for one seed; the reported record count includes all three seeds.

| Condition | Records | Original plan-slot accuracy | Counterfactual plan-slot accuracy | Decisive-cue recall | Counterfactual consistency | Preservation rate | Required-change accuracy | Unexpected-change rate | Citation-required grounded score (counterfactual) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Source-label oracle | 72 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| Text evidence + declared delta | 72 | 0.583 | 0.792 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| Shuffled delta | 72 | 0.583 | 0.792 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| Text evidence only | 72 | 0.583 | 0.417 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.505 |
| Citation echo control | 72 | 0.583 | 0.417 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.117 |
| Prior only | 72 | 0.958 | 0.417 | 0.000 | 0.000 | 0.667 | 0.000 | 0.333 | 0.000 |

The full ordinary metrics and per-seed summaries are in `runs/evidence_sensitivity/summary.json`; pair-level records are in `runs/evidence_sensitivity/records.jsonl`. The table above is generated from the summary and is included in the manuscript as `tab:evidence-sensitivity`.

## Interpretation and claim gate

The verifier passes the construction-level check: the source-label oracle identifies the decisive cue, applies the expected plan delta, and preserves all unrelated fields. The text evidence + declared delta control also passes the locality check, which verifies that the counterfactual scorer rewards the declared change when it is supplied directly. The shuffled-delta result is not an independent positive finding because every fixture delta is identical; it is retained as a diagnostic and explicitly marked as degenerate.

The remaining controls fail the decisive-cue test. Text and citation form recover some legal evidence and stable plan slots, but they do not identify the edited source cue. The prior-only predictor reaches high original plan-slot accuracy while failing required change accuracy and counterfactual consistency. This is the central anti-shortcut result: plan agreement on the source-key holdout does not establish source grounding or cue-sensitive planning.

Accordingly, this run supports only the following claims:

1. The released verifier distinguishes source-cue access from non-decisive text and citation controls on the controlled holdout.
2. The counterfactual locality checks are sensitive to the declared plan delta and expose the prior-only shortcut.
3. The oracle and lookup controls validate the measurement procedure; they do not establish performance for a trained speech model, listener judgments, waveform quality, or audio-conditioned generalization.
