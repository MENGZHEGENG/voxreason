# VoxReason Evidence-Sensitivity ICLR 2027 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn VoxReason into a claim-safe ICLR 2027 submission whose central result tests whether speech plans respond to decisive evidence edits while preserving unrelated fields.

**Architecture:** Keep the public benchmark and deterministic evaluator as the reproducibility boundary, and put licensed/private audio, learned-run manifests, and human-study material in the private project repository only. Build the evidence-sensitivity result from paired original/counterfactual cases, with ordinary accuracy and citation metrics reported alongside required-change and irrelevant-change metrics. Treat any incomplete learned run, proxy signal, synthetic-only result, or unverified audio path as diagnostic evidence and exclude it from deployment or best-paper claims.

**Tech Stack:** Python 3, pytest, JSON/JSONL benchmark manifests, existing VoxReason scorer and reproduction scripts, PyTorch/Hugging Face only in existing approved environments, LaTeX with the ICLR 2027 template, vector figures (SVG/PDF), and source-grounded review files.

**Spec:** This document is the execution specification for the GPT-6 evidence-grounded paper plan; the current benchmark and manuscript remain the source of truth for exact schemas and already-verified numbers.

## Execution status — 2026-09-12 18:10 EDT

Completed in the current working tree:

- The public benchmark audit, deterministic reproduction, guarded counterfactual scorer, focused tests, and full test run were executed.
- The evidence-sensitivity matrix completed six controlled conditions over three deterministic seeds and 24 source-key-disjoint pairs, yielding 432 expected, observed, and valid records with zero missing or duplicate rows.
- The claim-safe analysis, manuscript revision, evidence-sensitivity table, polished pre-synthesis schematic, rendered PDF checks, and three-skill local review cycle were completed.
- The compact evidence-sensitivity results figure was generated from the audited summary, exported as PDF and PNG, included in the manuscript, and inspected both standalone and in the rendered ten-page PDF.
- The two paper figures were redrawn into fresh `v2` revision directories using fixed-dimension vector-first exports, constrained layout, and the figure-builder/figure-QA workflow; the rendered PDF previews passed visual inspection with no overlap or clipping.
- The final manuscript source, claim analysis, results table and figure, QA record, local review records, and lightweight LaTeX dependencies were committed and pushed in `d942f38`; the execution-status update was pushed in `d7f7f95`.
- The final local review records the known four public-release-hygiene test failures; they arise from intentionally tracked manuscript/figure outputs and are not code or benchmark failures.
- An author-facing arXiv bundle was compiled independently from an isolated source tree with bundled Tectonic, round-trip compiled from `source.zip`, and passed `scripts/audit_release.py`.
- The verified arXiv PDF and source ZIP were copied to `/Users/gengm/Desktop/voxreason_arxiv_2026-09-12/` with matching SHA-256 checksums.

Pending before the broader paper can be declared finished:

- The user explicitly instructed this turn to ignore Claude, so no substantive Claude review was obtained. This is an explicit waiver for the urgent arXiv handoff, not completion of the required external review gate.
- The anonymous ICLR venue bundle remains deferred; the author-facing arXiv bundle is complete and audited.
- Incomplete learned-run summaries remain appendix diagnostics only; no learned-model ranking or training claim is promoted.
- A read-only staged-release audit utility and tests were added in commit `9474d02`; it checks source identity rules, private/legacy paths, archive traversal, and basic PDF/source closure. It is not a substitute for auditing the final bundles.

## Global Constraints

- Scope is `/Users/gengm/Documents/ChatGPT/Speech Xuewei/voxreason-patchwork-20260818-214303/repo`; do not inspect or modify sibling patchwork directories.
- Preserve existing untracked build, figure, run, and review outputs unless a targeted cleanup is explicitly justified.
- The public benchmark has 100 cases, a 67/17/16 split, two target utterances, one scene, two role labels, eight plan slots, and no public context audio; no acoustic-grounding claim may be made from it.
- The source-emotion prior result (24 source-key-holdout test cases: 0.9583 plan-slot accuracy, 0 counterfactual consistency, 1.0 unexpected-change rate, 0.6667 exact accuracy) is a motivating diagnostic, not a general learned-model result.
- Learned runs with 51 predictions and 249 missing cases per model are incomplete until manifests, coverage, denominators, and failure causes are audited; they must not be ranked as full-test results.
- No human listener, participant, or manual rating resource may be used without explicit user approval; prefer deterministic metrics, public benchmarks, and automated/model-based analysis.
- Every new experiment must have a fixed seed list, immutable input manifest, explicit denominator, saved config, and a result ledger distinguishing completed, missing, invalid, and excluded cases.
- Venue version is double-blind and nine-page main text; author-facing arXiv version preserves the author block and removes line numbers only. Both use the ICLR 2027 template unless a venue rule requires otherwise.
- Avoid unsupported claims, the prohibited c-word and its common inflections, and AI-sounding filler; use precise evidence, result, finding, observation, and limitation language.
- Any paper or release completion requires rendered PDF inspection, at least one Claude review, and the three-skill local review cycle (`academic-paper-review`, `academic-paper-reviewer`, `review-academic-paper`) for the final iteration.
- All generated PDFs must show page numbers unless the template forbids them; report final token usage and, for cluster work, GPU-hours with job IDs and accounting gaps.

---

### Task 1: Freeze the evidence ledger and executable plan

**Files:**
- Create: `docs/superpowers/plans/2026-09-11-voxreason-iclr2027-evidence-sensitivity.md`
- Inspect: `scripts/check_benchmark_files.py`, `scripts/reproduce_results.py`, `src/voxreason_public/results.py`, `paper/voxreason_full_polished.tex`
- Create or modify only after audit: `runs/evidence_sensitivity/manifest.json`, `runs/evidence_sensitivity/ledger.jsonl`

**Interfaces:**
- Consumes: existing case JSON files and scorer APIs; no schema changes until the audit identifies a concrete need.
- Produces: a versioned experiment manifest containing conditions, seed list, split, scorer version/hash, expected denominators, and exclusion policy; later tasks use the ledger as the only source for reported numbers.

- [x] **Step 1: Record the already-verified baseline.**

  Run:

  ```bash
  python3 scripts/check_benchmark_files.py
  python3 scripts/reproduce_results.py
  ```

  Copy only values printed by these commands into the ledger, preserving metric names and denominators. Record that the public cases contain no context audio and that source-label oracle performance is construction-level supervision, not a fair learned comparison.

- [x] **Step 2: Freeze the experiment manifest.**

  The manifest must enumerate `prior_only`, `source_label_oracle`, `text_evidence_only`, `text_evidence_counterfactual`, and each learned condition that is actually runnable. For each condition include `split`, `case_ids`, `seeds: [0, 1, 2]`, `input_fields`, `output_fields`, `metric_denominators`, `missing_policy: report_and_exclude_from_ranking`, and the exact command or entry point. Do not list a condition as complete before its ledger has one row per case and seed.

- [x] **Step 3: Run the manifest audit.**

  Check that every predicted case is in the declared split, every missing case is explicitly listed, duplicate case/seed rows are rejected, and aggregate metrics can be recomputed from the ledger. Fail closed if a result has an implicit denominator or mixes original and counterfactual cases without a pairing key.

- [x] **Step 4: Save a checkpoint.**

  ```bash
  git add docs/superpowers/plans/2026-09-11-voxreason-iclr2027-evidence-sensitivity.md runs/evidence_sensitivity
  git commit -m "docs: freeze VoxReason evidence sensitivity plan"
  ```

  Checkpoint recorded in the plan file at the current revision; the scorer and
  experiment harness checkpoints are recorded below by their commit IDs.

### Task 2: Make counterfactual scoring fail closed

**Files:**
- Modify: `src/voxreason_public/results.py` near the counterfactual scorer
- Test: `tests/test_results.py` or the repository's existing scorer test module
- Create if absent: `tests/test_counterfactual_scorer.py`

**Interfaces:**
- Consumes: paired gold plans and predicted plans using the existing plan-slot schema.
- Produces: counterfactual metrics that separately count required changes, preserved irrelevant fields, unexpected changes, and invalid/missing predictions; existing callers retain compatible metric keys unless a new key is additive.

- [x] **Step 1: Write failing tests for the two missing guards.**

  Add cases where (a) the prediction matches the original plan and fails to make a required target change, and (b) the prediction changes an irrelevant field while making the required change. Assert that required-change recall is zero in (a), irrelevant-preservation is zero in (b), and unexpected-change rate is one in (b). Add a test where no valid paired case exists and assert that the scorer returns an explicit zero-denominator status instead of a fabricated zero-quality result.

- [x] **Step 2: Run the focused tests.**

  ```bash
  python3 -m pytest -q tests/test_counterfactual_scorer.py
  ```

  Expected: the new tests fail against the current final-value-only check because it does not prove that the required field changed.

- [x] **Step 3: Implement the smallest scorer change.**

  Compare original and counterfactual gold slots to derive the required-change set and preserved-field set. Compare the prediction against both gold plans. Count a pair as required-change-correct only when every required slot takes the counterfactual value, and count preservation only when every preserved slot remains equal to the original value. Keep unexpected changes limited to slots that the gold pair says should remain unchanged. Carry `n_pairs`, `n_required_slots`, `n_preserved_slots`, `n_missing`, and `status` in the result.

- [x] **Step 4: Re-run focused and full tests.**

  ```bash
  python3 -m pytest -q tests/test_counterfactual_scorer.py
  python3 -m pytest -q
  ```

  The full suite may continue to report public-hygiene failures caused by private paper/build/run outputs. Preserve that distinction in the ledger and do not silently delete those outputs.

- [x] **Step 5: Commit the scorer guard.**

  ```bash
  git add src/voxreason_public/results.py tests/test_counterfactual_scorer.py tests/test_results.py
  git commit -m "fix: require paired counterfactual changes"
  ```

  Implemented in commit `296edbe`.

### Task 3: Run the decisive automated experiment matrix

**Files:**
- Create: `scripts/run_evidence_sensitivity.py`
- Create: `scripts/audit_experiment_coverage.py`
- Create: `tests/test_evidence_sensitivity.py`
- Create: `runs/evidence_sensitivity/README.md`
- Output only: `runs/evidence_sensitivity/*.jsonl`, `runs/evidence_sensitivity/summary.json`

**Interfaces:**
- Consumes: the frozen manifest and existing public case files.
- Produces: paired per-case records with `condition`, `seed`, `case_id`, `source_group`, `prediction_status`, `ordinary_metrics`, `required_change_metrics`, `preservation_metrics`, and `error_reason`; summary code emits macro averages plus source-grouped bootstrap intervals.

- [x] **Step 1: Write tests for pairing and denominators.**

  Verify that a seed with one missing case is reported as incomplete, that original/counterfactual records must share a `pair_id`, that source groups never cross train/dev/test boundaries, and that a summary reports both `n_total` and `n_valid`.

- [x] **Step 2: Run tests to establish the contract.**

  ```bash
  python3 -m pytest -q tests/test_evidence_sensitivity.py
  ```

- [x] **Step 3: Implement deterministic conditions first.**

  Run `prior_only`, source-label oracle, evidence-only, and controlled evidence-shuffle conditions over the declared holdout. Include a citation-echo control that receives citation-like strings without decisive evidence. Use the same pair IDs and evaluate all conditions with the guarded scorer.

- [ ] **Step 4: Add learned conditions only with complete coverage.**

  Reuse the existing approved environment and model checkpoints. Run exactly three seeds, save stdout/stderr and config hashes, and stop the condition from entering the ranking table if any seed is incomplete or if case coverage differs across conditions. No local download of large checkpoints or datasets is allowed.

- [x] **Step 5: Summarize uncertainty correctly.**

  Bootstrap by source group, not by individual utterance. Report paired differences, 95% intervals, valid-case counts, and missing-case counts. Never turn a missing prediction into a correct or incorrect label without an explicit pre-registered policy.

- [x] **Step 6: Commit only reproducibility-safe scripts and small ledgers.**

  ```bash
  git add scripts/run_evidence_sensitivity.py scripts/audit_experiment_coverage.py tests/test_evidence_sensitivity.py runs/evidence_sensitivity/README.md
  git commit -m "feat: add evidence sensitivity experiment harness"
  ```

  Implemented in commit `00f3a3a`.

### Task 4: Decide the claim gate and update the analysis

**Files:**
- Create: `paper/analysis/evidence_sensitivity_analysis.md`
- Modify: `paper/voxreason_full_polished.tex`
- Modify: `paper/references.bib` only for verified primary sources
- Create or modify: `paper/tables/evidence_sensitivity_table.tex`

**Interfaces:**
- Consumes: the completed ledger and guarded scorer summaries.
- Produces: a claim ledger mapping every headline sentence to an exact condition, denominator, and evidence status; the manuscript reports positive and negative evidence together.

- [x] **Step 1: Apply the kill gates.**

  Keep the evidence-sensitivity thesis only if at least one controlled evidence edit yields a measurable required-change/preservation gap and the effect survives source-grouped uncertainty analysis. Downgrade to a benchmark/audit paper if no condition improves paired success over the prior-only baseline. Stop any intervention-training claim if learned coverage is incomplete, if the effect appears only on synthetic controls, or if ordinary accuracy rises while paired success does not.

- [x] **Step 2: Write the analysis before rewriting claims.**

  For each table row include input condition, training/evaluation split, pair count, valid count, ordinary plan accuracy, required-change recall, irrelevant-field preservation, unexpected-change rate, and confidence interval. State that source-label oracle is an upper-bound diagnostic. Keep acoustic-grounding absent unless approved real audio is actually evaluated.

- [x] **Step 3: Revise the manuscript problem-first.**

  Use the sequence: why evidence-sensitive speech planning matters; why ordinary accuracy/citation scores are insufficient; the paired intervention and preservation protocol; benchmark and leakage boundaries; results with negative evidence; calibrated conclusions and limitations. Add a concise contributions section, explicit evaluation question, exact scope, and in-text `\ref` pointers for every figure/table.

- [x] **Step 4: Build the author-facing arXiv variant.**

  Built and audited `release/arxiv/` with the author block and `\iclrfinalcopy` preserved. The anonymous ICLR source remains a separate deferred deliverable.

- [x] **Step 5: Commit the analysis and manuscript revision.**

  ```bash
  git add paper/analysis/evidence_sensitivity_analysis.md paper/voxreason_full_polished.tex paper/tables/evidence_sensitivity_table.tex paper/references.bib
  git commit -m "paper: revise VoxReason around evidence sensitivity"
  ```

### Task 5: Produce and verify core figures and tables

**Files:**
- Modify/create: `paper/figures/revisions/pre_synthesis_schematic/`
- Create: `paper/figures/revisions/evidence_sensitivity_results/`
- Modify: `paper/tables/evidence_sensitivity_table.tex`
- Create: `paper/qa/figure_table_qa.md`

**Interfaces:**
- Consumes: the final ledger and manuscript labels.
- Produces: vector source plus PDF/SVG exports and a rendered QA record; all visual claims are traceable to ledger rows.

- [x] **Step 1: Keep the core problem schematic.**

  Show original evidence -> original plan, one decisive evidence edit -> counterfactual gold plan, and the two checks: required fields change, irrelevant fields stay fixed. Use consistent colors for evidence, plan, and audit; include no unsupported acoustic path.

- [x] **Step 2: Add one compact results figure.**

  Plot ordinary accuracy beside required-change recall, preservation, and unexpected-change rate for each complete condition. Show valid-case counts and intervals; visually mark incomplete learned conditions as excluded diagnostics rather than plotting them as comparable bars.

- [x] **Step 3: Render and inspect from at least two views.**

  Compile the paper, render the relevant PDF pages, and inspect both the page render and the standalone PDF/SVG. Check labels, legends, captions, arrows, clipping, font size, alignment, and single-page placement. Record findings in `paper/qa/figure_table_qa.md` and revise until no major overlap or readability issue remains.

- [x] **Step 4: Commit visual outputs that belong in the reproducibility release.**

  ```bash
  git add paper/figures paper/tables paper/qa/figure_table_qa.md
  git commit -m "fig: show paired evidence sensitivity results"
  ```

### Task 6: Execute the review-and-improvement cycle

**Files:**
- Create/update: `paper/reviews/academic_paper_review.md`
- Create/update: `paper/reviews/academic_paper_reviewer.md`
- Create/update: `paper/reviews/review_academic_paper.md`
- Create/update: `paper/reviews/claude_review.md`
- Modify: manuscript, analysis, figures, tables, and tests as required by actionable findings

**Interfaces:**
- Consumes: a rendered manuscript and complete claim ledger.
- Produces: issue-indexed reviews with severity, exact location, evidence, proposed fix, applied fix, and re-check status; the final iteration has no unresolved major blocker.

- [x] **Step 1: Run all three local review skills on the same revision.**

  `academic-paper-review` checks structure, literature, methodology, statistics, and claim safety; `academic-paper-reviewer` performs its full multi-perspective review and adjudication; `review-academic-paper` performs the independent rigorous review. Reviewers are read-only.

- [x] **Step 2: Apply every actionable major and moderate finding.**

  Update the manuscript, analysis, scripts, or experiment only when the finding is in scope and reproducibly testable. Re-run the affected tests and rebuild the PDF.

- [x] **Step 3: Repeat the complete three-skill cycle.**

  Do not treat a partial or single-skill pass as completion. Track each finding across iterations until closed or documented as genuinely infeasible with its impact on claims.

- [ ] **Step 4: Obtain at least one Claude review.**

  Not obtained because the user explicitly instructed this turn to ignore Claude. The waiver permits the urgent arXiv handoff but does not satisfy this paper-completion gate.

- [ ] **Step 5: Commit review files and fixes.**

  ```bash
  git add paper/reviews paper/voxreason_full_polished.tex paper/analysis
  git commit -m "review: close VoxReason paper blockers"
  ```

### Task 7: Final reproducibility, release, and completion audit

**Files:**
- Modify: `README.md` or existing reproducibility documentation
- Create: `release/iclr2027/` and `release/arxiv/` only after the manuscript is final
- Create/update: private-project step log in the private repository, if a paired private repository is configured

**Interfaces:**
- Consumes: final source, scripts, small public-safe outputs, review records, and rendered PDFs.
- Produces: an anonymous venue bundle, an author-facing arXiv PDF plus complete source ZIP, and a completion record with finish time, token usage, experiment status, and GPU-hour accounting.

- [x] **Step 1: Run all deterministic checks.**

  ```bash
  python3 scripts/check_benchmark_files.py
  python3 scripts/reproduce_results.py
  python3 -m pytest -q
  ```

  Classify any failure as code, data, release-hygiene, or environment and do not hide release-hygiene findings by deleting private evidence.

- [x] **Step 2: Verify rendered PDFs.**

  Confirm page numbers on every page including appendices, figure/table placement, references, author-block policy, line-number policy, and absence of accidental private paths, credentials, or large assets. Keep the source ZIP limited to reproducible source, bibliography, figures, tables, and required lightweight assets.

- [x] **Step 3: Run the public-release hygiene audit.**

  `python3 scripts/audit_release.py release/arxiv --kind arxiv` passed. The source archive contains only the manuscript, lightweight style files, table source, and the two final vector figures; private run metadata, cluster paths, human-study data, and incomplete model outputs are excluded.

- [x] **Step 4: Record resource and token accounting.**

  This arXiv handoff used no cluster jobs and therefore incurred 0 GPU-hours. Codex goal usage at the handoff was approximately 3.5M tokens; the UI counter is cumulative across continuations and is not a per-command measurement.

- [ ] **Step 5: Mark completion only after all gates pass.**

  The project is complete only when benchmark checks pass, headline experiments are complete and denominator-safe, manuscript and figures are rendered and reviewed, Claude review is complete, release bundles are audited, and all remaining limitations are visible in the paper. If any gate remains pending, report the exact blocker and keep the goal active.

## Self-review checklist

- [ ] Every requested component is covered: latest plan, new experiments, best-paper-oriented writing, figures, local review cycle, Claude gate, and release audit.
- [ ] No placeholder task language is used; every experiment has named files, conditions, metrics, seeds, tests, and commands.
- [ ] The plan keeps the public/private boundary and incomplete learned coverage explicit.
- [ ] The plan does not authorize human evaluation or large local downloads.
- [ ] Every claimed result will be traceable to a case-level ledger and rendered output.
