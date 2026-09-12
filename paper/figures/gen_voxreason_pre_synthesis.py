#!/usr/bin/env python3
"""Generate the VoxReason pre-synthesis evidence-path figure.

The diagram is rendered from exact text with Matplotlib so that
the PDF/SVG outputs remain reproducible and the labels cannot be silently
altered by an image generator.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path(__file__).resolve().parent
FIGURE_STEM = OUT_DIR / "voxreason_pre_synthesis"

BG = "#FFFFFF"
INK = "#27313B"
MUTED = "#61707D"
CONNECTOR = "#6C7884"
PANEL = "#F5F7F8"
PANEL_EDGE = "#D4DCE2"
CASE_FILL = "#EAF2F8"
CASE_EDGE = "#6E8294"
PLANNER_FILL = "#FFF1D9"
PLANNER_EDGE = "#C58C45"
VERIFY_FILL = "#E7F4F0"
VERIFY_EDGE = "#4F8B7B"
CHECK_FILL = "#EEF1F8"
CHECK_EDGE = "#6B7D9B"


def add_box(ax, x, y, width, height, *, fill, edge, title_lines, body_lines,
            title_size=20, body_size=13.5, dashed=False):
    """Add a rounded, text-safe node using top-left figure coordinates."""
    linestyle = (0, (7, 5)) if dashed else "-"
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=20",
        linewidth=2.5,
        linestyle=linestyle,
        edgecolor=edge,
        facecolor=fill,
        zorder=2,
    )
    ax.add_patch(patch)

    center_x = x + width / 2
    title_start = y + 34 if len(title_lines) == 1 else y + 27
    for index, line in enumerate(title_lines):
        ax.text(
            center_x,
            title_start + index * 27,
            line,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=INK,
            zorder=3,
        )

    body_start = y + (94 if len(title_lines) == 1 else 105)
    for index, line in enumerate(body_lines):
        ax.text(
            center_x,
            body_start + index * 30,
            line,
            ha="center",
            va="center",
            fontsize=body_size,
            color=INK,
            zorder=3,
        )


def add_arrow(ax, start, end, *, dashed=False, mutation_scale=17):
    linestyle = (0, (7, 5)) if dashed else "-"
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=2.6,
        linestyle=linestyle,
        color=CONNECTOR,
        shrinkA=0,
        shrinkB=0,
        zorder=1,
    )
    ax.add_patch(arrow)


def add_orthogonal_arrow(ax, points):
    """Draw an orthogonal connector and put the arrowhead on its last leg."""
    xs, ys = zip(*points)
    ax.plot(xs, ys, color=CONNECTOR, linewidth=2.6, zorder=1)
    add_arrow(ax, points[-2], points[-1], mutation_scale=17)


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    fig, ax = plt.subplots(figsize=(16, 8.2), dpi=180)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1600)
    ax.set_ylim(820, 0)
    ax.axis("off")

    # The top band groups the measured, text-and-plan path. The lower nodes
    # are intentionally outside it because they record downstream or audit
    # outputs rather than additional planner stages.
    panel = FancyBboxPatch(
        (40, 40),
        1520,
        350,
        boxstyle="round,pad=0.02,rounding_size=26",
        linewidth=2.5,
        edgecolor=PANEL_EDGE,
        facecolor=PANEL,
        zorder=0,
    )
    ax.add_patch(panel)

    ax.text(
        72,
        82,
        "Pre-synthesis evidence path",
        ha="left",
        va="center",
        fontsize=22,
        fontweight="bold",
        color=INK,
        zorder=3,
    )
    ax.text(
        1525,
        82,
        "same case ID · one cue edited",
        ha="right",
        va="center",
        fontsize=14,
        color=MUTED,
        zorder=3,
    )

    node_y = 150
    node_h = 170
    add_box(
        ax, 75, node_y, 225, node_h,
        fill=CASE_FILL, edge=CASE_EDGE,
        title_lines=["Case record"],
        body_lines=["turn · role · scene", "source-labeled cue"],
        title_size=20,
    )
    add_box(
        ax, 365, node_y, 275, node_h,
        fill=PLANNER_FILL, edge=PLANNER_EDGE,
        title_lines=["Typed planner"],
        body_lines=["delivery slots + citations", "affect · intent · prosody"],
        title_size=20,
        body_size=13.3,
    )
    add_box(
        ax, 705, node_y, 220, node_h,
        fill=VERIFY_FILL, edge=VERIFY_EDGE,
        title_lines=["Verifier"],
        body_lines=["citation validity", "plan-slot agreement"],
        title_size=20,
        body_size=13.2,
    )
    add_box(
        ax, 980, node_y, 220, node_h,
        fill=VERIFY_FILL, edge=VERIFY_EDGE,
        title_lines=["One-cue edit"],
        body_lines=["cue locality", "all other slots fixed"],
        title_size=19.5,
        body_size=13.2,
    )
    add_box(
        ax, 1240, node_y, 285, node_h,
        fill=CHECK_FILL, edge=CHECK_EDGE,
        title_lines=["Listener-independent", "checks"],
        body_lines=["cue coverage", "citation requirement"],
        title_size=16.0,
        body_size=12.7,
    )

    # Main sequence arrows sit entirely in the gaps between nodes.
    add_arrow(ax, (300, 235), (350, 235))
    add_arrow(ax, (640, 235), (690, 235))
    add_arrow(ax, (925, 235), (965, 235))
    add_arrow(ax, (1200, 235), (1230, 235))

    # Lower outputs have a clear relationship to the measured path.
    add_box(
        ax, 365, 510, 340, 175,
        fill=BG, edge=CONNECTOR,
        title_lines=["Waveform path"],
        body_lines=["downstream only", "excluded from current claims"],
        title_size=19,
        body_size=13.1,
        dashed=True,
    )
    add_box(
        ax, 760, 485, 670, 220,
        fill=BG, edge=CONNECTOR,
        title_lines=["Evidence record"],
        body_lines=["verifier ledger", "validity · agreement · locality"],
        title_size=20,
        body_size=13.4,
    )

    # Dashed means that waveform synthesis is downstream of the current
    # evidence claim. The solid orthogonal routes show what is recorded.
    add_arrow(ax, (502.5, 320), (502.5, 500), dashed=True, mutation_scale=16)
    add_orthogonal_arrow(ax, [(815, 320), (815, 425), (930, 425), (930, 485)])
    add_arrow(ax, (1090, 320), (1090, 475))
    add_orthogonal_arrow(ax, [(1382.5, 320), (1382.5, 425), (1300, 425), (1300, 485)])

    # Keep the canvas boundary clean in all export formats.
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(FIGURE_STEM.with_suffix(".pdf"), facecolor=BG)
    fig.savefig(FIGURE_STEM.with_suffix(".svg"), facecolor=BG)
    fig.savefig(FIGURE_STEM.with_suffix(".png"), dpi=220, facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    main()
