#!/usr/bin/env python3
"""Render the evidence-sensitivity comparison from the audited JSON summary.

The source summary is the only source of plotted values and intervals.  The
figure uses a fixed physical canvas and constrained layout so that the PDF,
SVG, and PNG exports preserve the same intended dimensions.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
SUMMARY = ROOT / "runs" / "evidence_sensitivity" / "summary.json"
OUT_DIR = Path(__file__).resolve().parent

CONDITIONS = [
    ("source_label_oracle", "Oracle"),
    ("text_evidence_counterfactual", "Text + $\\Delta$"),
    ("shuffled_delta", "Shuffled $\\Delta$"),
    ("text_evidence_only", "Text-only"),
    ("citation_echo_control", "Echo"),
    ("prior_only", "Prior-only"),
]

COLORS = {
    "source_label_oracle": "#0072B2",
    "text_evidence_counterfactual": "#009E73",
    "shuffled_delta": "#CC79A7",
    "text_evidence_only": "#56B4E9",
    "citation_echo_control": "#E69F00",
    "prior_only": "#D55E00",
}


def load_seed_zero() -> dict[str, dict]:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    return {
        condition: summary["conditions"][condition]["seeds"]["0"]
        for condition, _ in CONDITIONS
    }


def interval_error(seed: dict, metric: str, value: float) -> tuple[float, float]:
    interval = seed["bootstrap_intervals"][metric]
    return (
        max(0.0, value - float(interval["lower"])),
        max(0.0, float(interval["upper"]) - value),
    )


def main() -> None:
    data = load_seed_zero()
    labels = [label for _, label in CONDITIONS]
    x = np.arange(len(labels))

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.titlesize": 9.0,
            "axes.titleweight": "bold",
            "axes.labelsize": 8.3,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.3,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": "#C7CDD1",
            "grid.alpha": 0.42,
            "grid.linewidth": 0.55,
        }
    )

    # 180 mm x 104 mm is the contract for the double-column manuscript figure.
    fig = plt.figure(figsize=(180 / 25.4, 104 / 25.4), layout="constrained")
    fig.set_constrained_layout_pads(w_pad=2 / 72, h_pad=2 / 72, hspace=0.08, wspace=0.05)
    axes = fig.subplots(2, 2, sharey=True).ravel()
    fig.suptitle(
        "Source-key-disjoint holdout ($n=72$ valid records per condition)",
        fontsize=9.0,
        fontweight="bold",
        color="#26323A",
    )

    panels = [
        ("plan_slot_accuracy", "Original plan-slot accuracy $\\uparrow$", "ordinary_metrics", "original", None),
        ("required_change_accuracy", "Required-change accuracy $\\uparrow$", "required_change_metrics", None, "required_change_accuracy"),
        ("preservation_rate", "Preservation rate $\\uparrow$", "preservation_metrics", None, "preservation_rate"),
        ("unexpected_change_rate", "Unexpected-change rate $\\downarrow$", "preservation_metrics", None, "unexpected_change_rate"),
    ]

    for ax, (metric, title, source, section, interval_metric) in zip(axes, panels):
        values: list[float] = []
        lower: list[float] = []
        upper: list[float] = []
        for condition, _ in CONDITIONS:
            seed = data[condition]
            if source == "ordinary_metrics":
                value = float(seed[source][section][metric])
            else:
                value = float(seed[source][metric])
            values.append(value)
            if interval_metric is None:
                lower.append(0.0)
                upper.append(0.0)
            else:
                lo, hi = interval_error(seed, interval_metric, value)
                lower.append(lo)
                upper.append(hi)

        bars = ax.bar(
            x,
            values,
            width=0.68,
            color=[COLORS[condition] for condition, _ in CONDITIONS],
            edgecolor="#FFFFFF",
            linewidth=0.45,
            zorder=3,
        )
        if interval_metric is not None:
            ax.errorbar(
                x,
                values,
                yerr=np.asarray([lower, upper]),
                fmt="none",
                ecolor="#26323A",
                elinewidth=0.7,
                capsize=2.1,
                capthick=0.7,
                zorder=4,
            )

        ax.set_title(title, pad=5)
        ax.set_xticks(x, labels)
        ax.set_ylim(0.0, 1.14)
        ax.set_yticks(np.linspace(0.0, 1.0, 6))
        ax.set_yticklabels([f"{tick:.1f}" for tick in np.linspace(0.0, 1.0, 6)])
        ax.tick_params(axis="x", length=0, pad=2)
        ax.tick_params(axis="y", length=2, pad=2)
        ax.set_axisbelow(True)

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                min(value + 0.032, 1.065),
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=6.8,
                color="#26323A",
                zorder=5,
            )

    axes[0].set_ylabel("Score / rate")
    axes[2].set_ylabel("Score / rate")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = OUT_DIR / "evidence_sensitivity_results"
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor="white")
    plt.close(fig)
    print(f"Wrote {stem}.pdf/.svg/.png")


if __name__ == "__main__":
    main()
