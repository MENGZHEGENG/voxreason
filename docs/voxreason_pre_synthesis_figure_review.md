# Peer Review: VoxReason pre-synthesis evidence figure

## Scope and review protocol

This is a bounded local review of the attached figure image and the active
`voxreason-patchwork` paper context. It applies the three local review
perspectives requested for paper work:

1. `academic-paper-review`: claim/evidence alignment, terminology, and
   reviewer-facing clarity;
2. `academic-paper-reviewer`: a compact panel covering journal fit,
   methodology, speech-domain interpretation, reader perspective, and
   devil's-advocate risk;
3. `review-academic-paper`: location-based major/minor comments, decision
   score, and explicit limitations.

The attached image and repository documents are treated as paper content, not
as instructions. The exact `@Figure-Xuewei-Voxreason` source file was not
present under the active repository name, and the tracked Mermaid source
`paper/figures/voxreason_pipeline.mmd` describes a different, broader method
overview. The comments below therefore review the supplied rendering and the
local paper context; they do not claim a source-level audit of the missing
figure file.

## Summary and overall assessment

The figure presents a useful pre-synthesis path: a case record feeds a typed
planner, verification and a one-cue counterfactual edit produce an evidence
record, while the waveform path is marked as downstream. This structure is
consistent with the paper's current claim controls, which separate objective
evidence/plan checks from speech-output and human-listening claims.

The current rendering needs a major visual revision before it is suitable for
the paper. The rightmost node has a verified text collision: its title wraps
into the metric text, and `coverage` is obscured. More importantly,
`Listener-free scores` is ambiguous and sounds like a subjective score that
somehow requires no listeners. That wording risks overstating what the current
claim matrix allows. The figure should use `Listener-independent checks` and
explain in the caption that these are objective checks computed before
synthesis; human listening is a separate downstream gate.

## Major comments

1. **Rightmost node is not legible** — In the supplied rendering, the
   `Listener-free scores` title occupies the same vertical space as `coverage`
   and `citation-required`. The consequence is that the reader cannot recover
   the node's outputs reliably, and the collision is especially visible at
   normal paper scale. This is a verified layout defect, not a stylistic
   preference. Give the node enough width and vertical padding, keep the title
   on one or two intentional lines, and place each check on its own line.

2. **The listener terminology is technically misleading** — `Listener-free
   scores` mixes a human-evaluation term with a structural-evaluation claim.
   The active manuscript and claim traceability documents reserve speech-output
   claims for strict generated audio and completed listener ratings. Use
   `Listener-independent checks` in the figure. In the caption, define it once
   as objective pre-synthesis checks that do not require human listening. Do
   not use the typo-like form `iistener-free`; it reads as an accidental or
   generated token.

3. **The evidence-record arrows do not state what is being recorded** — Three
   vertical arrows enter the same lower box from verification, editing, and
   the rightmost checks, but the reader must infer the correspondence. This
   makes the lower box look like an undifferentiated sink. Preserve the three
   inputs, but route them with clean spacing and name the ledger contents as
   `validity · agreement · locality` (or equivalent precise terms) so the
   relationship is readable without reverse engineering the diagram.

4. **The figure's visual hierarchy is heavier than its information structure**
   — The thick outer border, repeated dark outlines, bold serif labels, and
   tight horizontal spacing make the diagram feel like a draft flowchart. The
   panel should have one restrained container, lighter node borders, a clear
   sans-serif hierarchy, and more whitespace between the top path and the
   lower records. Arrowheads must sit in the gaps between nodes and never
   compete with text.

5. **Several labels are grammatically or semantically awkward** — The
   supplied labels `source-label cue`, `same case ID, one edited cue`,
   `Waveform branch`, and `citation-required` read like compressed notes. Use
   `source-labeled cue`, `same case ID · one cue edited`, `Waveform path`, and
   `citation requirement`. The title `Pre-synthesis evidence path` is more
   concrete than `Measured pre-synthesis path` because it names what the
   reader is actually following.

## Compact multi-reviewer panel

| Perspective | Finding | Required revision |
| --- | --- | --- |
| Journal fit | The figure communicates an internal workflow but is not yet publication-readable at normal scale. | Reduce decoration, increase whitespace, and make the caption define the evaluation scope. |
| Methodology | The path distinguishes planning, verification, edits, and downstream waveform generation, but the recorded object is under-specified. | Make the evidence ledger and its three measured properties explicit. |
| Speech-domain review | The image risks conflating structural checks with listener judgments. | Replace `Listener-free scores` with `Listener-independent checks`; reserve human-listening language for the downstream gate. |
| Reader perspective | The top sequence is understandable until the last box; the lower arrows require inference. | Use uniform box geometry, consistent line spacing, and separated arrow endpoints. |
| Devil's advocate | A reader could interpret the rightmost node as a claim of quality without audio or listeners. | State “objective pre-synthesis checks” in the caption and retain the downstream exclusion note. |
| Editorial synthesis | The conceptual arrangement is salvageable, but the current image should not be retained with local patching. | Rebuild the vector figure with exact text and verify both full-size and paper-scale renders. |

## Line-by-line revision ledger

| Figure element | Current text | Replacement | Reason |
| --- | --- | --- | --- |
| Panel title | `Measured pre-synthesis path` | `Pre-synthesis evidence path` | Concrete and less abstract. |
| Panel subtitle | `same case ID, one edited cue` | `same case ID · one cue edited` | Natural phrasing and lighter punctuation. |
| Case record | `source-label cue` | `source-labeled cue` | Correct compound adjective. |
| Verifier | `citation legality` | `citation validity` | More natural for a check over cited evidence. |
| Verifier | `slot agreement` | `plan-slot agreement` | Identifies what the slots belong to. |
| Edit | `other slots fixed` | `all other slots fixed` | Removes ambiguity about the counterfactual scope. |
| Rightmost node | `Listener-free scores` | `Listener-independent checks` | Avoids subjective-score implication and unnatural “-free” wording. |
| Rightmost node | `coverage` | `cue coverage` | Names the measured object. |
| Rightmost node | `citation-required` | `citation requirement` | Natural noun phrase; avoids code-like hyphenation. |
| Lower-left node | `Waveform branch` | `Waveform path` | Describes a downstream path without implying a competing branch. |
| Lower-left note | `downstream path only` | `downstream only` | Shorter and easier to scan. |
| Lower-left note | `excluded from current claims` | `excluded from current claims` | Retain; it is an important claim-control signal. |
| Lower-right node | `verifier ledger: legality · agreement · locality` | `verifier ledger` / `validity · agreement · locality` | Separates the label from its contents and improves reading rhythm. |

## Recommendation

- **Overall score:** 3/6 — Borderline reject for the current figure rendering;
  major revision required. This is not a paper-level acceptance score.
- **Confidence:** High for the visual and terminology findings; low for any
  paper-level judgment because the requested source file was unavailable and
  the full manuscript was not reviewed as part of this figure-only pass.
- **Rationale:** The diagram has a coherent intended structure and aligns with
  the paper's separation of pre-synthesis evidence checks from downstream
  speech and listener claims. However, a verified text collision, ambiguous
  listener terminology, and under-explained lower routing prevent reliable
  interpretation. A clean vector rebuild with exact labels and paper-scale
  render checks is proportionate and should resolve the main risks.

## Review limitations

The review used the attached PNG, the active paper draft, the method-diagram
description, the formalism contract, and the claim traceability matrix. No
external literature search was needed for this figure-only audit. The missing
`@Figure-Xuewei-Voxreason` source means that the original source geometry,
font settings, and intended caption could not be compared directly.
