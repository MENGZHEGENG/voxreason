# Figure 1 brief — pre-synthesis evidence path, revision v2

Takeaway: VoxReason evaluates a typed delivery plan against explicit source
evidence and a one-cue counterfactual before any waveform is produced.

Question: What is held fixed, what changes, and which listener-independent
checks are reported before synthesis?

Figure class: compact conceptual schematic with an evidence ledger.

Evidence and allowed transformations: node labels and directed edges are
transcribed from the benchmark protocol in `paper/voxreason_full_polished.tex`
and the verifier/reproduction scripts. The drawing contains no measured
values. The waveform path is shown only as downstream context and is excluded
from current claims.

Contract: 180 mm x 108 mm, vector PDF/SVG plus a 300 dpi PNG preview, intended
for the ICLR 2027 manuscript and its author-facing arXiv version. The figure
uses 8.5 pt base text and a 7.5 pt lower-bound screen. These are provisional
manuscript defaults; final rendered size is checked in the compiled PDF.

Required notation: `cue locality`, `all other slots fixed`, `citation`, and
`listener-independent` must remain explicit. The ledger row must distinguish
validity/agreement, locality, and cue coverage/citation requirement.

Topology: the upper row is the left-to-right evaluation flow
`case_record -> typed_planner -> verifier -> one_cue_edit -> listener_checks`.
The planner also points down to the downstream-only waveform path; the
verifier, one-cue edit, and listener checks each point down to their matching
evidence-ledger record. Arrows are data/evaluation flow; no training edge or
gradient is implied.

Unknowns and limits: geometry checks cannot validate the benchmark science;
the source protocol and manuscript remain the semantic authority. The figure
does not certify listener preference, synthesis quality, or broad waveform
understanding.
