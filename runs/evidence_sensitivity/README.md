# Evidence-sensitivity matrix

This directory contains a deterministic, paired audit of the public
source-key holdout. Each row in `records.jsonl` joins one original case and
one counterfactual edit through `pair_id`; missing or invalid predictions stay
in the ledger and are excluded from metric means.

Run the matrix from the repository root with:

```bash
python3 scripts/run_evidence_sensitivity.py \
  --bootstrap-samples 10000 \
  --output-dir runs/evidence_sensitivity
python3 scripts/audit_experiment_coverage.py
```

The manifest is the denominator contract. It records the split, source groups,
pair identities, seeds, input/output fields, missing-data policy, and metric
denominators. The audit fails if a declared condition/seed/pair row is absent,
duplicated, assigned to the wrong split or source group, or inconsistent with
the summary counts and macro means.

Conditions:

- `prior_only`: source-emotion lookup trained on the source-key-disjoint
  training split, with no cited evidence.
- `source_label_oracle`: construction-level upper bound that copies released
  gold evidence and plans.
- `text_evidence_only`: target-text and role-profile lookup with public
  textual/role cues, without the decisive source cue.
- `text_evidence_counterfactual`: controlled positive that applies the
  declared edit to the text lookup plan.
- `citation_echo_control`: text lookup with a citation-like, non-decisive cue.
- `shuffled_delta`: seeded delta-permutation diagnostic. The current fixture
  has identical edit deltas, so this control is explicitly degenerate and is
  not evidence of learned robustness.

The results are planning-stage measurements on derived public labels. They do
not evaluate listener judgments, waveform quality, or general audio
understanding, and they do not redistribute the source audio.
