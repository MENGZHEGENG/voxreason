# Figure brief: Pre-synthesis evidence path with split ledger entries

## Takeaway and reader question

The figure should make one point immediately: VoxReason checks whether a
planner grounds structured speaking decisions in permitted source cues before
synthesis, and whether a controlled one-cue edit changes only the linked plan
fields. The reader should be able to answer: “What is checked before a
waveform exists, and which evidence-record entry receives each check?”

## Figure class and scope

- **Class:** conceptual method/evidence-path schematic.
- **Primary use:** paper method overview or benchmark-scope figure.
- **Claim scope:** planning-stage evidence validity, plan-slot agreement, cue
  locality, cue coverage, and citation requirements.
- **Explicit exclusion:** the waveform path is downstream only and is excluded
  from the current structural claims. Human listening and listener preference
  are not represented as measured outputs in this figure.
- **Data status:** no numerical values are plotted; there are no axes, units,
  uncertainty intervals, or statistical comparisons.

## Source and evidence basis

The semantic contract is grounded in the supplied figure image, the prior
local figure review, and the active public benchmark documentation:

- `README.md`, especially “What You Can Check” and “Claim Boundary”;
- `BENCHMARK.md`, especially “Task Variants”, “Metrics”, and “What This
  Benchmark Does Not Answer”;
- `schemas/benchmark_case.schema.json`, for case records, cues, plans, and
  counterfactual edits;
- `docs/voxreason_pre_synthesis_figure_review.md`, for the line-by-line
  terminology and routing corrections.

The exact `@Figure-Xuewei-Voxreason` source file was not found in the active
repository, so the original source geometry and font settings remain unknown.
This rebuild preserves the reviewed semantic structure and does not infer
missing numerical or experimental content.

## Target size and requirements check

- **Canvas:** 180 mm × 108 mm, single page, intended as a provisional
  double-column-width figure.
- **Typography:** 8.5 pt requested size, 7.5 pt minimum floor; deliberate line
  breaks keep node labels readable at the intended width.
- **Venue:** no venue was specified. Official venue requirements were not
  available in the repository and were not checked on 2026-09-11.
- **Style:** restrained color-coded rounded-node vector schematic, with the
  bundled `render_schematic.py` retained as the geometry gate; semantics and
  geometry are kept in separate JSON files.

## Exact visible text

The visible node text is defined verbatim in `figure.spec.json`:

- `Case record` / `turn · role · scene` / `source-labeled cue`
- `Typed planner` / `delivery slots +` / `citations` /
  `affect · intent ·` / `prosody`
- `Verifier` / `citation` / `validity` / `plan-slot` / `agreement`
- `One-cue edit` / `cue locality` / `all other slots fixed`
- `Listener-` / `independent` / `checks` / `cue coverage` /
  `citation requirement`
- `Waveform path` / `downstream only` / `excluded from current` / `claims`
- three `Evidence record` entries for `validity · agreement`, `locality`, and
  `cue coverage · citation requirement`.

The phrase is intentionally **“Listener-independent checks”**. It does not
use “Listener-free scores” or the typo-like “iistener-free”. The caption
defines these as objective pre-synthesis checks and keeps human listening as a
separate downstream evaluation gate.

## Semantic node and edge contract

### Nodes

1. `case_record`: source-labeled case context, turn/role/scene metadata, and
   the cue presented to the planner.
2. `typed_planner`: structured delivery slots and citations, including affect,
   intent, and prosody.
3. `verifier`: citation validity and agreement between the plan and licensed
   slots.
4. `one_cue_edit`: a target-preserving counterfactual in which one cue changes
   and all unrelated slots are expected to remain fixed.
5. `listener_checks`: objective checks for cue coverage and citation
   requirement; no human listening is implied.
6. `waveform_path`: a downstream synthesis path retained as a scope-control
   marker, not as evidence for the current planning claims.
7. `evidence_validity`: the evidence-record entry for citation validity and
   plan-slot agreement.
8. `evidence_locality`: the evidence-record entry for one-cue locality.
9. `evidence_coverage`: the evidence-record entry for cue coverage and
   citation requirement.

### Directed edges

1. `case_record -> typed_planner`: supplies the case and licensed cue context.
2. `typed_planner -> verifier`: sends the typed plan and citations for checks.
3. `verifier -> one_cue_edit`: passes the verified plan into the controlled
   edit path.
4. `one_cue_edit -> listener_checks`: evaluates the edited plan against the
   cue-specific expectations.
5. `typed_planner -> waveform_path`: marks synthesis as downstream of the
   planning path.
6. `verifier -> evidence_validity`: records validity and agreement evidence.
7. `one_cue_edit -> evidence_locality`: records locality evidence.
8. `listener_checks -> evidence_coverage`: records cue coverage and citation
   requirement checks.

All connectors are forward path links. No connector is a training-only link,
gradient link, or human-rating result. The split ledger entries are one
evidence record represented as three non-overlapping destinations; this keeps
the source-to-record correspondence visible.

## Composition choice

Two compositions were considered:

- **A — compact horizontal pipeline with a lower split ledger lane:** keeps the
  main planning sequence readable and gives every evidence input its own
  target. This is selected.
- **B — one large evidence box with three incoming arrows:** preserves the
  original visual metaphor, but the bundled rectangular renderer's named top
  port would force all three arrowheads to overlap. It is rejected because the
  collision obscures provenance.

The selected layout uses generous gaps, aligned lower ledger entries, and one
diagonal downstream marker. The arrows are kept visually separate even at
the evidence-record boundary.

## Caption content

See `caption.md`. The caption must retain the scope statement that these are
objective pre-synthesis checks and do not replace human listening evaluation.
