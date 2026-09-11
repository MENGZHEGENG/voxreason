# Paper Project Scoped Instructions

Apply this file at the root of a manuscript, paper-review, rebuttal, proposal, or research-writing repository or subdirectory.

## Paper Review GitHub Handoff

- When working on academic paper reviews, manuscript critiques, reviewer reports, rebuttal notes, or related research-paper review outputs, treat saving and pushing the completed review outputs to GitHub properly and regularly as a required part of the workflow.
- Use the user's GitHub username `MENGZHEGENG` when identifying the expected GitHub account, fork owner, or remote owner for paper-review handoff.
- Before pushing paper-review work, inspect `git status`, verify the active branch and remote, and confirm that only intentional review outputs, notes, source documents, or supporting metadata are included.
- Push at sensible checkpoints after coherent review updates, especially before ending a session, switching tasks, or making major revisions to review conclusions.
- Do not include private manuscripts, confidential peer-review materials, copyrighted PDFs, reviewer identities, credentials, or sensitive metadata unless the user explicitly confirms they should be committed to that repository.
- Do not force-push, rewrite history, or create/switch branches unless the user explicitly asks or approves it.
- If a GitHub remote, branch, credentials, network access, or publication/privacy concern blocks pushing, report the blocker and provide the exact commands or setup needed to complete the handoff safely.
- If the user explicitly says not to push for a specific paper-review task, follow that instruction and clearly note that the global paper-review handoff was skipped by request.

## Claude Paper Review Checks

- Whenever Claude is called to review an academic paper, manuscript, technical report, rebuttal, or related research writing, explicitly ask Claude to double-check whether the paper sounds ChatGPT-written or AI-written.
- The Claude review prompt should ask for concrete flags on AI-sounding phrasing, generic transitions, template-like structure, over-polished claims, and unnatural reviewer-facing prose, plus revision suggestions that preserve technical meaning and evidence.
- When Claude is called for paper review, also ask it to check figure and table layout quality: captions must not be too close to figures or tables, spacing and alignment should look polished, and every figure/table should be visually clear and publication-quality.
- Treat this AI-writing-sound check as mandatory alongside the scientific, technical, and presentation review; do not omit it unless the user explicitly asks to skip style or AI-writing review for that specific Claude call.

## Multi-Reviewer Cleanup

- When a multi-reviewer academic review is completed, stop or close all reviewer subagents after their final review outputs have been collected, and do this before moving on to another task or ending the session.
- Do not leave reviewer subagents running in the background after the multi-reviewer review is complete; if a reviewer subagent cannot be stopped, report the blocker clearly.

## Academic Paper Writing Style

- When writing, revising, or polishing academic papers, follow the writing style, structure, tone, and level of technical detail used in the user's reference papers listed at `https://scholar.google.ca/citations?user=RS59rgIAAAAJ&hl=en`.
- Do not open, scrape, or call the Google Scholar profile page during normal writing-skill use because it is slow and unnecessary.
- Prefer the local style cache at `/Users/gengm/.codex/style-guides/RS59rgIAAAAJ/`, including cached notes, open-access examples, user-provided PDFs/LaTeX/source text, or previously extracted style notes from those papers.
- If no local examples or extracted notes are available, ask the user to provide representative papers, PDFs, BibTeX entries, or writing samples rather than fetching the Google Scholar page.
- Preserve the target venue's required format when it conflicts with the reference-paper style, but keep the prose style and technical exposition as close as appropriate.
- Academic writing should be as easy to follow as possible. Prefer clear structure, explicit motivation, smooth transitions, well-scoped claims, and reader-oriented explanations that make the method, evidence, and conclusions easy to track without oversimplifying the technical content.
- Research papers and proposals must not sound like sales documents or promotional reports. Avoid marketing-style words and phrases such as `seamlessly`, `cutting-edge`, `game-changing`, `revolutionary`, `unlock`, `empower`, `transform`, or similar promotional language unless directly quoted from a source or explicitly required by the user.
- Avoid using the word `deliberately` in academic, proposal, report, and public-facing research writing unless it is directly quoted from a source or explicitly required by the user; replace it with a more precise context-specific phrase when needed.
- When writing papers, proposals, reports, or data descriptions, avoid using the word `row` unless it is directly quoted from a source, required by a data format, or explicitly requested by the user; prefer context-specific alternatives such as `entry`, `sample`, `record`, `instance`, `example`, `observation`, or `case`.
- When writing papers, proposals, reports, or data descriptions, avoid using informal version labels such as `v1`, `v2`, `version 1`, `version 2`, or similar unless they are part of an official dataset/model name, directly quoted from a source, required for exact reproducibility, or explicitly requested by the user; prefer descriptive names such as `initial release`, `revised dataset`, `training split`, `evaluation split`, or the official release name.
- When writing papers, proposals, reports, or data descriptions, avoid vague meta phrases such as `evidence boundary`, `evidence boundaries`, `data boundary`, `boundary of evidence`, or similar wording unless it is a formal technical term, directly quoted from a source, or explicitly requested by the user; use precise descriptions of scope, assumptions, dataset coverage, inclusion criteria, limitations, or evaluation setting instead.
- When writing, revising, or polishing academic papers, treat modal verbs such as `can` and `should` carefully. Use `can` only for supported capability claims, use `should` only for justified recommendations or implications, and replace vague modal wording with precise evidence-backed wording when possible.
- Pay close attention to the use of dashes in academic writing. Avoid conspicuous overuse of em dashes or dash-heavy sentence patterns, because they can make the text read as AI-generated; prefer clearer sentence structure, commas, parentheses, or full stops unless a dash is genuinely the best punctuation choice.
- Include the GitHub repository link as a footnote in the introduction of academic papers when a project repository exists or is intended for release, unless the venue forbids it or the user explicitly asks not to include it.
- Do not use report-like tables in academic papers, proposals, or supplements. Avoid business-style status tables, project-management summaries, KPI dashboards, checklist grids, meeting-note tables, or other report-form layouts unless the venue explicitly requires them; prefer prose, figures, or academically standard result/ablation/example tables instead.
- When drawing or revising figures, ensure dots, markers, arrows, connectors, and labels do not overlap or obscure important content. Check spacing, alignment, arrow routing, marker placement, and label readability carefully before finalizing any figure.
- Every table and figure in a paper, report, appendix, or supplement must have an explicit in-text pointer. Reference each table or figure by number/name in the surrounding text and explain what the reader should take from it; do not leave standalone tables or figures without a textual callout.
- Check all formulas very carefully in papers, proposals, reports, slides, and figures. Pay special attention to notation consistency, indices, dimensions, operators, superscripts, subscripts, Greek letters, signs, normalization terms, and whether formulas embedded in figures exactly match the text and intended meaning.
