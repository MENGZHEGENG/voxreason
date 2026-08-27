#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


PIPELINE = r"""
\begin{tikzpicture}[
  font=\small,
  box/.style={draw=black!55, rounded corners=2pt, line width=0.45pt, align=center, minimum width=2.45cm, minimum height=0.92cm, fill=white},
  cue/.style={box, fill=blue!6},
  model/.style={box, fill=teal!7},
  eval/.style={box, fill=orange!10},
  arrow/.style={-{Latex[length=2.2mm]}, line width=0.55pt, draw=black!65},
  dashedarrow/.style={-{Latex[length=2.2mm]}, line width=0.55pt, draw=black!55, dashed}
]
\node[cue] (input) {Dialogue\\speech cues\\role context};
\node[model, right=0.7cm of input] (evidence) {Evidence\\selection};
\node[model, right=0.7cm of evidence] (planner) {Structured\\speaking plan};
\node[eval, right=0.7cm of planner] (metrics) {Faithfulness\\metrics};
\node[eval, below=0.72cm of planner] (counter) {Counterfactual\\cue edits};
\node[model, above=0.72cm of planner] (reward) {Process\\supervision};

\draw[arrow] (input) -- node[above, font=\scriptsize] {licensed labels} (evidence);
\draw[arrow] (evidence) -- node[above, font=\scriptsize] {cited cues} (planner);
\draw[arrow] (planner) -- node[above, font=\scriptsize] {JSON slots} (metrics);
\draw[dashedarrow] (counter) -- node[right, font=\scriptsize] {expected slot changes} (metrics);
\draw[dashedarrow] (input.south) to[out=-50,in=180] (counter.west);
\draw[arrow] (metrics.north) to[out=110,in=0] (reward.east);
\draw[arrow] (reward.west) to[out=180,in=90] (evidence.north);
\node[draw=black!25, fill=gray!4, rounded corners=3pt, inner sep=6pt, fit=(input)(evidence)(planner)(metrics)(counter)(reward)] {};
\end{tikzpicture}
""".strip()


CLAIM_SCOPE = r"""
\begin{tikzpicture}[
  font=\small,
  box/.style={draw=black!55, rounded corners=2pt, line width=0.45pt, align=left, text width=0.42\linewidth, fill=white, inner sep=5pt},
  title/.style={font=\bfseries\small},
]
\node[box, fill=green!6] (inside) {\textbf{Claims supported here}\\
$\bullet$ evidence precision/recall/F1\\
$\bullet$ speaking-plan slot accuracy\\
$\bullet$ counterfactual cue consistency\\
$\bullet$ representation and source-label checks};
\node[box, fill=red!5, right=0.08\linewidth of inside] (outside) {\textbf{Deferred validation}\\
$\bullet$ listener studies\\
$\bullet$ generated-audio user judgments\\
$\bullet$ real-world release decisions\\
$\bullet$ claims needing recruited raters};
\node[above=0.15cm of inside, font=\scriptsize\scshape, text=green!45!black] {listener-free evidence};
\node[above=0.15cm of outside, font=\scriptsize\scshape, text=red!55!black] {future study};
\end{tikzpicture}
""".strip()


def main() -> None:
    figure_dir = ROOT / "paper/figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    (figure_dir / "fig_pipeline.tex").write_text(PIPELINE + "\n", encoding="utf-8")
    (figure_dir / "fig_claim_scope.tex").write_text(CLAIM_SCOPE + "\n", encoding="utf-8")
    print("wrote paper/figures/fig_pipeline.tex")
    print("wrote paper/figures/fig_claim_scope.tex")


if __name__ == "__main__":
    main()
