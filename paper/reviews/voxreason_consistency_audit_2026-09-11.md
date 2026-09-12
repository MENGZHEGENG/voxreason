# Peer Review: VoxReason: Listener-Free Evaluation of Source-Grounded Speech Planning Before Synthesis

## Summary and overall assessment

This focused local audit checks the current manuscript, the authored arXiv source and PDF, the source ZIP, and the polished pre-synthesis schematic. The paper presents a source-grounded speech-planning benchmark with typed plans, citation-aware verification, one-cue counterfactual edits, and deterministic anti-shortcut diagnostics. The strongest aspect is the disciplined separation between pre-synthesis plan verification and claims about rendered speech or listener perception. The current figure is readable and publication-oriented, with no detected text, arrow, box, clipping, or overflow collisions. The main remaining issue is cross-file terminology drift, followed by a small set of localized clarity and release-metadata issues.

## Major comments

1. **Unify the listener terminology across the paper and release metadata.** — The title, PDF metadata, `README.md`, and `CITATION.cff` use “Listener-Free,” while the introduction, Figure 1, and its caption use “listener-independent” (manuscript lines 62, 131, and 136; figure brief lines 68–69). This is a verified consistency problem, not a scientific contradiction, but it makes the reader wonder whether the two terms denote different evaluation settings. The remembered title “Listener-Independent Evaluation...” is a reasonable canonical choice if that is the intended project name. If so, change the title and all release metadata together; otherwise retain “Listener-Free” and rename the body and figure label to “listener-free checks.” Whichever term is retained, define it once as “no human listening judgments in the primary score,” and use it consistently. Note that “listener-independent” can also imply invariance across listeners, so “listener-free” is semantically clearer for the stated protocol.

## Minor comments

1. **Abstract, decisive-cue sentence (manuscript line 53).** — “The contrast recovers the decisive cue from 0.000 to 1.000” is grammatically ambiguous because the contrast itself does not recover a cue. Replace it with a direct metric statement, for example: “Decisive-cue recall is 0.000 for the text-only control and 1.000 for the oracle reference.”

2. **Abstract, learned-planner implication (line 53).** — “Isolates the information that a learned planner must use” is slightly stronger than the demonstrated evidence because no complete learned-planner result is available. A safer formulation is “shows the information exposed to a learned planner by the source-label task” or “identifies the information needed to pass the verifier.”

3. **Undefined `CF` shorthand (line 221).** — The Table 2 header uses “CF consistency,” although `CF` is not expanded in the manuscript. Spell out “Counterfactual consistency” in the header or define `CF` in the caption. Spelling it out is preferable because the table is small enough to accommodate it.

4. **Undefined `SFT` shorthand (Appendix line 291).** — Expand “supervised fine-tuning (SFT)” at first use, or spell out “source-labeled supervised fine-tuning” in the two table entries. The same shorthand appears in `README.md` lines 121–122.

5. **Normalize `labeled`/`labelled`.** — The figure, main text, and most release text use US spelling (“source-labeled”), while the Appendix and learned-run README entries use “source-labelled” (manuscript lines 291–292; `README.md` lines 121–122). Choose one house style and apply it across prose, tables, captions, and metadata.

6. **Clarify the status of the “source-label upper bound.”** — The manuscript correctly explains at line 168 that this condition receives gold evidence and a gold plan and is a deterministic reference, not a learned model. Because “upper bound” can be read as an attainable model guarantee, consider renaming it to “source-label oracle” or “gold source-label reference,” or repeat “oracle reference” in the main-results table caption and README.

7. **Restrict the reproducibility claim to primary results (line 176).** — “All values in this paper are regenerated...” is broader than the later qualification that learned-run summaries are partial diagnostics. Replace it with “All primary reported values...” and explicitly exclude the incomplete learned-run summaries in the same paragraph.

8. **Define the auxiliary acoustic checks at first mention (lines 75 and 127).** — “Acoustic preflight” and “source-label acoustic-anchor check” are understandable but initially underspecified. Add a short definition such as “repository-level consistency checks over derived acoustic statistics,” and keep the existing statement that they do not support perceptual or rendered-speech claims.

9. **Remove a small AI-like phrasing risk in the scope sentence (line 62).** — “It does not mean that the benchmark measures speech quality without a listener model” is harder to parse than necessary and could suggest a learned listener model that the paper does not use. Prefer “It does not assess speech quality without human judgments; it measures source attribution and plan consistency before synthesis.”

10. **Synchronize figure provenance status.** — The polished figure has clean geometry and a clean styled-text report, and the rendered PNG is visually readable. However, its manifest still says `visual_review: PENDING` and `scientific_review: PENDING` at lines 58–59, while the separate figure review records the completed local inspection. Update those fields to the project’s final status vocabulary before release so automated readers do not interpret the artifact as unaudited.

11. **Release hygiene for legacy figure variants.** — The current paper references the polished3 PDF, and the authored ZIP contains the current vector figure only. Older figure revisions remain in the repository but are not referenced. This is not a manuscript defect; before a public release, keep the final bundle restricted to the referenced figure or mark legacy variants clearly as archival.

## Recommendation

- **Overall score:** 5 — Accept
- **Confidence:** High for the local consistency and rendered-artifact checks; Medium for broader venue-level assessment
- **Rationale:** The central measurement protocol, claim scope, figure layout, and reproducibility paths are coherent and claim-safe. The identified issues are localized and can be fixed without new experiments. The terminology mismatch should be resolved before submission because it affects the paper title, figure, abstract framing, and citation metadata simultaneously.

## Review limitations

This was a focused local audit, not a fresh external literature or novelty-priority review. The local three-pass protocol was applied using the academic-paper-review, academic-paper-reviewer, and review-academic-paper skills. The authored PDF was checked with PDF metadata and text extraction, and the current figure was checked from its rendered PNG plus machine-readable geometry and styled-text reports. A required Claude review was attempted previously but remains pending because the service reported a session-limit reset time of 12:20 AM America/Toronto.
