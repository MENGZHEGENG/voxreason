# Figure review: pre-synthesis evidence path

## Revision and scope

Final revision stem: `pre_synthesis_evidence_path_polished3`.

This revision was rebuilt from the semantic specification in `figure.spec.json`
and the explicit geometry in `figure.layout.json`. The content was checked
against the attached figure and the current public VoxReason repository
documentation (`README.md`, `BENCHMARK.md`, and
`schemas/benchmark_case.schema.json`). The exact source file named
`@Figure-Xuewei-Voxreason` was not available in the workspace; the attached
PNG was therefore treated as the visual source, while the local documentation
provided the claim boundary. The figure remains a planning-stage schematic and
does not claim synthesized-speech quality or listener preference.

Intended export size is 180 x 108 mm on one page. The requested body text size
is 8.5 pt; the smallest rendered text is 7.5 pt for compact annotations.

## Review status

| Review item | Status | Evidence or limitation |
|---|---|---|
| Scientific semantics and claim boundary | PASS | Matches the reviewed planning-stage path; the exact source file was unavailable, so source-specific intent beyond the attached PNG was not checked. |
| Values, units, uncertainty | NOT CHECKED / N/A | Conceptual schematic; no numeric results, units, or uncertainty intervals are displayed. |
| Layout and geometry | PASS | Bundled geometry checker reports `errors=[]` and `warnings=[]`. |
| Typography and glyphs | PASS | Manual PDF/PNG render inspection and styled text audit pass; the embedded-font inventory was not available. |
| Connector routing and crossings | PASS | Top flow is direct; lower evidence routes are orthogonal and split into three ledger cards with no visible knot or crossing. |
| Export and page size | PASS | One-page PDF; `pdfinfo` reports 180 x 108 mm and matching page boxes. |
| Grayscale readability | PASS | Independent grayscale preview inspected; structure and labels remain distinguishable without color. |
| PDF/SVG geometry and content parity | PASS | Independent PyMuPDF SVG render matches the PDF geometry and visible content. |
| PDF/SVG typography parity | NOT CHECKED | PyMuPDF uses a serif fallback for the editable SVG text; Inkscape/RSVG was unavailable, so native SVG typography was not independently validated against the PDF font rendering. |
| PDF preflight and font inventory | NOT CHECKED | The QA preflight could not run because `pdffonts` is not installed; `pdftotext` and `pdfimages` are also unavailable. |
| Reproducibility and provenance | PASS | Semantic spec, layout spec, builder checker, styled renderer, caption, manifest, geometry report, and styled text report are included. |

## Edge transcription and meaning

| Edge | Meaning |
|---|---|
| `case_record -> typed_planner` | Supplies the case context and licensed source-labeled cue. |
| `typed_planner -> verifier` | Sends the typed delivery plan and citations for validity and agreement checks. |
| `verifier -> one_cue_edit` | Passes the verified plan into the controlled one-cue edit. |
| `one_cue_edit -> listener_checks` | Evaluates cue-specific expectations for the edited plan. |
| `typed_planner -> waveform_path` | Marks the downstream synthesis path, which is outside the current structural claims. |
| `verifier -> evidence_validity` | Records validity and plan-slot agreement in the verifier ledger. |
| `one_cue_edit -> evidence_locality` | Records the locality of the one-cue edit. |
| `listener_checks -> evidence_coverage` | Records cue coverage and the citation requirement. |

## Defects fixed

- Removed the rightmost text collision and gave the final node enough width and
  line spacing for `Listener-independent checks`.
- Replaced the awkward and typo-like `iistener-free` / `Listener-free scores`
  wording with the natural, claim-safe label `Listener-independent checks`.
- Replaced compressed labels such as `source-label cue`, `citation legality`,
  `slot agreement`, and `other slots fixed` with readable wording.
- Replaced the single lower evidence box and its converging arrow knot with
  three separated ledger entries for validity/agreement, locality, and
  coverage/citation.
- Kept the bundled geometry checker active. Its synthetic
  `FancyArrowPatch` `CLOSEPOLY` vertices are ignored only for the checker’s
  arrow/text intersection test; actual node, route, text, and crossing checks
  remain active.

## Rendered evidence inspected

The following independent outputs were inspected after rendering:

- PDF page preview: `qa_manual/polished3-pdf-preview.png`
- Exported PNG: `pre_synthesis_evidence_path_polished3.png`
- Grayscale PDF preview: `qa_manual/polished3-grayscale.png`
- Lower ledger crop: `qa_manual/polished3-ledger-crop.png`
- Right-node crop: `qa_manual/polished3-right-crop.png`
- Independently rendered editable SVG: `qa_manual/polished3-svg-preview.png`

## Deliverable decision

**READY FOR AUTHOR'S FINAL REVIEW.**

The figure is suitable for author inspection as a polished, editable vector
schematic. It is not marked fully submission-ready because the target venue’s
final figure requirements and embedded-font inventory were not provided or
verified, and the exact original source file was unavailable.

## Output hashes

SHA-256 hashes for the final exports:

```text
pre_synthesis_evidence_path_polished3.pdf
e1222d93446b1c696ceb068fa3deeb1803ffbbd6dbd7928a7721de558c5e223b

pre_synthesis_evidence_path_polished3.svg
e657c4417aae5b12121639165efb70e1746186d7d0b4caec0a3d790dbbd2d5d8

pre_synthesis_evidence_path_polished3.png
5da219e4b413768bf8ad249dda01464accea2648a76ec769eed371aea6f2afc9
```
