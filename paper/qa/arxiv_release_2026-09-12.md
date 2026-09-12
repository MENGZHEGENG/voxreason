# VoxReason arXiv release record

Date: 2026-09-12

## Deliverables

- Staged PDF: `release/arxiv/paper.pdf`
- Staged source archive: `release/arxiv/source.zip`
- Desktop handoff folder: `/Users/gengm/Desktop/voxreason_arxiv_2026-09-12/`
- Desktop files: `voxreason_arxiv.pdf` and `voxreason_arxiv_source.zip`

## Verification

- Author-facing source retains the author block and `\iclrfinalcopy`; no line-number switch is enabled.
- The author block is preserved in the staged and Desktop arXiv source/PDF handoff; the anonymous ICLR bundle is a separate venue variant and does not replace this author-facing artifact.
- Bundled Tectonic compilation from the isolated release source succeeded with 10 pages.
- Fresh unpack-and-compile of `source.zip` succeeded with 10 pages.
- `python3 scripts/audit_release.py release/arxiv --kind arxiv` passed.
- PDF metadata: letter size, 10 pages, unencrypted. Rendered pages 1, 6, and 10 were visually inspected; page numbers are visible and the figure/table/reference pages are readable.
- SHA-256 PDF: `dae3747d9c48c1f30e7312f765e94a449eebf1caa47be846dfdbdec850f382d0`
- SHA-256 source ZIP: `301ca1e9b23e58db5f99c841f57a5f9305a58d246f1f6a30afa2d7868ffdac0d`

## Scope note

This is an author-facing arXiv handoff. The user explicitly instructed the agent to ignore Claude for this urgent delivery, so no substantive Claude review is claimed. The anonymous ICLR bundle and external Claude review remain pending for full paper completion.

## Accounting

No cluster jobs were used for this handoff: 0 GPU-hours. Codex goal usage was approximately 3.5M cumulative tokens at handoff; the UI counter spans multiple continuations and is not a per-command measurement.
