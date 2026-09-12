# Peer Review: VoxReason: Listener-Independent Evaluation of Source-Grounded Speech Planning Before Synthesis

## Summary and overall assessment

This focused local audit checks the current manuscript, the authored arXiv source and PDF, the source ZIP, and the polished pre-synthesis schematic. The paper presents a source-grounded speech-planning benchmark with typed plans, citation-aware verification, one-cue counterfactual edits, and deterministic anti-shortcut diagnostics. The strongest aspect is the disciplined separation between pre-synthesis plan verification and claims about rendered speech or listener perception. The current figure is readable and publication-oriented, with no detected text, arrow, box, clipping, or overflow collisions. The earlier cross-file terminology issue and the listed localized clarity issues were re-checked after revision; no new manuscript blocker was found.

## Major comments

1. **Resolved terminology alignment.** — The manuscript title, PDF metadata, `README.md`, and `CITATION.cff` now use “Listener-Independent,” and the manuscript defines the term operationally as no human listening judgments in the primary score. The earlier mismatch is closed; this item no longer blocks release.

## Minor comments

1. **Abstract, decisive-cue sentence (manuscript line 53).** — “The contrast recovers the decisive cue from 0.000 to 1.000” is grammatically ambiguous because the contrast itself does not recover a cue. Replace it with a direct metric statement, for example: “Decisive-cue recall is 0.000 for the text-only control and 1.000 for the oracle reference.”

2. **Abstract, learned-planner implication (re-checked).** — The revised wording remains bounded by the complete deterministic matrix and does not promote incomplete learned outputs to a learned-model result.

3. **Counterfactual terminology (re-checked).** — Counterfactual metrics are spelled out or defined at their first substantial use in the current manuscript and table.

4. **`SFT` shorthand (re-checked).** — The current manuscript defines supervised fine-tuning (SFT) before the shorthand is used in the appendix.

5. **Spelling normalization (re-checked).** — Source-labeled terminology is consistent across the current manuscript and release-facing documentation.

6. **Source-label reference status (closed).** — The condition is consistently presented as a deterministic oracle/reference and not as a learned model.

7. **Reproducibility scope (closed).** — The current text distinguishes primary regenerated values from incomplete learned-run diagnostics.

8. **Auxiliary acoustic checks (closed).** — Their repository-level consistency role and non-perceptual scope are defined.

9. **Scope wording (closed).** — The current scope sentence states directly that the primary evaluation is pre-synthesis planning and does not assess speech quality or listener preference.

10. **Figure provenance status (closed for local review).** — The final results figure has clean geometry and styled-text checks, and its standalone and compiled-page renders were inspected. The release audit must still select only the final export.

11. **Release hygiene for legacy figure variants.** — This remains a release-packaging action, not a manuscript defect: the final bundles should include only the referenced vector export and required reproducibility files.

## Recommendation

- **Overall score:** 5 — Accept
- **Confidence:** High for the local consistency and rendered-output checks; Medium for broader venue-level assessment
- **Rationale:** The central measurement protocol, claim scope, figure layout, and reproducibility paths are coherent and claim-safe. The earlier terminology and clarity findings were addressed or explicitly bounded; the remaining work is the required external review and final release packaging.

## Review limitations

This was a focused local audit, not a fresh external literature or novelty-priority review. The local three-pass protocol was applied using the academic-paper-review, academic-paper-reviewer, and review-academic-paper skills after the final wording patch. The authored PDF was checked with PDF metadata and text extraction, and the current figure was checked from its rendered PNG plus machine-readable geometry and styled-text reports. A required Claude review remains pending until the previously reported session-limit reset time of 12:20 AM America/Toronto.
