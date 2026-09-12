#!/usr/bin/env python3
"""Generate the compact evidence-sensitivity results figure.

The figure is derived directly from the audited JSON summary so that every
displayed value and interval remains traceable to the reproducible run.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "runs" / "evidence_sensitivity" / "summary.json"
OUTPUT_DIR = ROOT / "paper" / "figures" / "revisions" / "evidence_sensitivity_results"

CONDITIONS = [
    ("source_label_oracle", "Oracle"),
    ("text_evidence_counterfactual", "Text + declared\ndelta"),
    ("shuffled_delta", "Shuffled\ndelta"),
    ("text_evidence_only", "Text only"),
    ("citation_echo_control", "Citation echo"),
    ("prior_only", "Prior only"),
]

# Okabe--Ito colors keep the comparison readable in common forms of color
# vision deficiency while giving the construction-level oracle a clear anchor.
COLORS = {
    "source_label_oracle": "#0072B2",
    "text_evidence_counterfactual": "#009E73",
    "shuffled_delta": "#CC79A7",
    "text_evidence_only": "#56B4E9",
    "citation_echo_control": "#E69F00",
    "prior_only": "#D55E00",
}


def load_seed_zero() -> dict[str, dict]:
    """Load one deterministic seed; all three seeds are identical by design."""
    summary = json.loads(SUMMARY.read_text())
    return {
        condition: details["seeds"]["0"]
        for condition, _ in CONDITIONS
        for details in [summary["conditions"][condition]]
    }


def error_bounds(seed: dict, metric: str, value: float) -> tuple[np.ndarray, np.ndarray]:
    """Return asymmetric 95% bootstrap error bars from the released summary."""
    interval = seed["bootstrap_intervals"][metric]
    lower = max(0.0, value - float(interval["lower"]))
    upper = max(0.0, float(interval["upper"]) - value)
    return np.asarray([lower]), np.asarray([upper])


def main() -> None:
    data = load_seed_zero()
    # Short tick labels keep the multi-panel chart legible; the caption and
    # the legend retain the complete condition names.
    labels = ["Oracle", "Text + $\\Delta$", "Shuffled $\\Delta$", "Text-only", "Echo", "Prior-only"]
    x = np.arange(len(CONDITIONS))

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.titlesize": 9.2,
            "axes.titleweight": "bold",
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.2,
            "ytick.labelsize": 7.4,
            "savefig.dpi": 300,
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

    panels = [
        ("original", "Original plan-slot accuracy $\\uparrow$", "ordinary", None),
        (
            "required_change_metrics",
            "Required-change accuracy $\\uparrow$",
            "required_change_accuracy",
            "required_change_accuracy",
        ),
        (
            "preservation_metrics",
            "Preservation rate $\\uparrow$",
            "preservation_rate",
            "preservation_rate",
        ),
        (
            "preservation_metrics",
            "Unexpected-change rate $\\downarrow$",
            "unexpected_change_rate",
            "unexpected_change_rate",
        ),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(7.05, 4.05), sharey=True)
    axes = axes.ravel()
    fig.subplots_adjust(left=0.065, right=0.995, bottom=0.22, top=0.87, wspace=0.14, hspace=0.60)
    fig.text(
        0.5,
        0.965,
        "Source-key-disjoint holdout ($n=72$ valid records per condition)",
        ha="center",
        va="top",
        fontsize=9.2,
        fontweight="bold",
        color="#26323A",
    )

    for ax, (source, title, metric, interval_metric) in zip(axes, panels):
        values = []
        yerr_low = []
        yerr_high = []
        for condition, _ in CONDITIONS:
            seed = data[condition]
            if source == "original":
                value = float(seed["ordinary_metrics"]["original"]["plan_slot_accuracy"])
            else:
                value = float(seed[source][metric])
            values.append(value)
            if interval_metric is None:
                yerr_low.append(0.0)
                yerr_high.append(0.0)
            else:
                low, high = error_bounds(seed, interval_metric, value)
                yerr_low.append(float(low[0]))
                yerr_high.append(float(high[0]))

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
                yerr=np.asarray([yerr_low, yerr_high]),
                fmt="none",
                ecolor="#26323A",
                elinewidth=0.7,
                capsize=2.1,
                capthick=0.7,
                zorder=4,
            )

        ax.set_title(title, pad=7)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0.0, 1.13)
        ax.set_yticks(np.linspace(0.0, 1.0, 6))
        ax.set_yticklabels([f"{tick:.1f}" for tick in np.linspace(0.0, 1.0, 6)])
        ax.tick_params(axis="x", length=0, pad=3)
        ax.tick_params(axis="y", length=2, pad=2)
        ax.set_axisbelow(True)

        for bar, value in zip(bars, values):
            y = min(value + 0.035, 1.065)
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=7.0,
                color="#26323A",
                rotation=0,
                zorder=5,
            )

    axes[0].set_ylabel("Score / rate")
    fig.text(
        0.5,
        0.035,
        "Bars show means; whiskers are 95% source-group bootstrap intervals. Incomplete learned-run outputs are excluded.",
        ha="center",
        va="bottom",
        fontsize=7.0,
        color="#4F5B63",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUTPUT_DIR / "evidence_sensitivity_results.pdf"
    png_path = OUTPUT_DIR / "evidence_sensitivity_results.png"
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"Wrote {pdf_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
