#!/usr/bin/env python3
"""Render the reviewed VoxReason schematic with a restrained paper style.

The semantic contract and routes remain in ``figure.spec.json`` and
``figure.layout.json``.  The bundled schematic renderer is run first as the
independent geometry gate; this file only supplies the final visual styling.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as MplPath

BUILDER_SCRIPTS = Path("/Users/gengm/.codex/skills/academic-figure-builder/scripts")
sys.path.insert(0, str(BUILDER_SCRIPTS))
import figurekit as kit  # noqa: E402
import render_schematic as bundled  # noqa: E402


BG = "#FFFFFF"
INK = "#26323B"
MUTED = "#647483"
CONNECTOR = "#6E7D89"
PANEL = "#F6F8F9"
PANEL_EDGE = "#D2DBE1"
CASE_FILL = "#EAF3F8"
CASE_EDGE = "#70899B"
PLANNER_FILL = "#FFF2DC"
PLANNER_EDGE = "#C68F3E"
VERIFY_FILL = "#E7F4F0"
VERIFY_EDGE = "#4C8E7D"
CHECK_FILL = "#EEF1F8"
CHECK_EDGE = "#7083A7"
AUDIT_FILL = "#FFFFFF"
AUDIT_EDGE = "#7A8792"


TEXT_LAYOUT = {
    "case_record": (["Case record"], ["turn · role · scene", "source-labeled cue"]),
    "typed_planner": (["Typed planner"], ["delivery slots +", "citations", "affect · intent ·", "prosody"]),
    "verifier": (["Verifier"], ["citation", "validity", "plan-slot", "agreement"]),
    "one_cue_edit": (["One-cue edit"], ["cue locality", "all other slots fixed"]),
    "listener_checks": (["Listener-", "independent", "checks"], ["cue coverage", "citation requirement"]),
    "waveform_path": (["Waveform path"], ["downstream only", "excluded from current", "claims"]),
    "evidence_validity": (["Evidence record"], ["validity · agreement"]),
    "evidence_locality": (["Evidence record"], ["locality"]),
    "evidence_coverage": (["Evidence record"], ["cue coverage ·", "citation requirement"]),
}

NODE_STYLE = {
    "case_record": (CASE_FILL, CASE_EDGE),
    "typed_planner": (PLANNER_FILL, PLANNER_EDGE),
    "verifier": (VERIFY_FILL, VERIFY_EDGE),
    "one_cue_edit": (VERIFY_FILL, VERIFY_EDGE),
    "listener_checks": (CHECK_FILL, CHECK_EDGE),
    "waveform_path": (BG, CONNECTOR),
    "evidence_validity": (AUDIT_FILL, AUDIT_EDGE),
    "evidence_locality": (AUDIT_FILL, AUDIT_EDGE),
    "evidence_coverage": (AUDIT_FILL, AUDIT_EDGE),
}


def points_from_report(report: dict, edge_id: str):
    return [tuple(point) for point in report["edge_routes_mm"][edge_id]]


def add_node(ax, node_id: str, rect: tuple[float, float, float, float], *, dashed=False):
    x0, y0, x1, y1 = rect
    fill, edge = NODE_STYLE[node_id]
    patch = FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=0,rounding_size=2.4",
        linewidth=1.15,
        linestyle=(0, (3.4, 2.6)) if dashed else "-",
        edgecolor=edge,
        facecolor=fill,
        zorder=2,
    )
    ax.add_patch(patch)

    title_lines, body_lines = TEXT_LAYOUT[node_id]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    title_step = 3.5
    body_step = 3.35
    if len(title_lines) == 1:
        title_start, body_start = cy + 6.3, cy + 1.7
    elif len(title_lines) == 2:
        title_start, body_start = cy + 7.2, cy - 0.6
    else:
        title_start, body_start = cy + 7.5, cy - 4.0
    title_size = 10.8 if node_id != "listener_checks" else 10.0
    if node_id.startswith("evidence_"):
        title_size = 9.7
    if node_id == "waveform_path":
        title_size = 10.0
    body_size = 8.5 if not node_id.startswith("evidence_") else 8.0
    if node_id == "waveform_path":
        body_size = 8.0

    for index, line in enumerate(title_lines):
        ax.text(cx, title_start - index * title_step, line, ha="center", va="center",
                fontsize=title_size, fontweight="bold", color=INK, zorder=3)
    for index, line in enumerate(body_lines):
        ax.text(cx, body_start - index * body_step, line, ha="center", va="center",
                fontsize=body_size, color=INK, zorder=3)


def add_route(ax, points, *, dashed=False):
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(points) - 1)
    patch = FancyArrowPatch(
        path=MplPath(points, codes),
        arrowstyle="-|>",
        mutation_scale=10.5,
        linewidth=1.15,
        linestyle=(0, (3.4, 2.6)) if dashed else "-",
        color=CONNECTOR,
        shrinkA=0,
        shrinkB=0,
        zorder=1,
    )
    ax.add_patch(patch)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Output stem without extension")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    spec = bundled.read_json(args.spec)
    layout = bundled.read_json(args.layout)
    kit.reserve_outputs(args.out, (".pdf", ".svg", ".png", ".manifest.json", ".geometry.json", ".styled_text_report.json"), args.force)

    # Keep the renderer's local correction for Matplotlib's synthetic arrow
    # CLOSEPOLY vertex, which otherwise creates a false text intersection.
    original_intersects = MplPath.intersects_bbox
    def corrected_intersects(self, bbox, filled=False):
        if self.codes is not None and len(self.codes) >= 2 and self.codes[-1] == MplPath.CLOSEPOLY:
            return MplPath(self.vertices[:-1], self.codes[:-1]).intersects_bbox(bbox, filled=filled)
        return original_intersects(self, bbox, filled=filled)

    MplPath.intersects_bbox = corrected_intersects
    try:
        with matplotlib.rc_context({
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.usetex": False,
            "savefig.bbox": None,
        }):
            checker_fig, report = bundled.construct(spec, layout)
            plt.close(checker_fig)
            if report["errors"]:
                kit.write_json(str(args.out) + ".geometry.json", report)
                print("GEOMETRY FAILED; no styled export written.", file=sys.stderr)
                for error in report["errors"]:
                    print("  " + error, file=sys.stderr)
                return 2

            fig = plt.figure(figsize=(spec["canvas_mm"][0] / 25.4, spec["canvas_mm"][1] / 25.4), dpi=180)
            fig.patch.set_facecolor(BG)
            ax = fig.add_axes((0, 0, 1, 1))
            ax.set(xlim=(0, spec["canvas_mm"][0]), ylim=(0, spec["canvas_mm"][1]), aspect="equal")
            ax.set_axis_off()

            ax.add_patch(FancyBboxPatch(
                (2, 56), 176, 48,
                boxstyle="round,pad=0,rounding_size=3.6",
                linewidth=1.1,
                edgecolor=PANEL_EDGE,
                facecolor=PANEL,
                zorder=0,
            ))
            ax.text(5, 99.6, "Pre-synthesis evidence path", ha="left", va="center",
                    fontsize=10.8, fontweight="bold", color=INK, zorder=3)
            ax.text(175.5, 99.6, "same case ID · one cue edited", ha="right", va="center",
                    fontsize=7.5, color=MUTED, zorder=3)

            rects = report["nodes_mm"]
            for node_id in spec["nodes"]:
                add_node(ax, node_id["id"], rects[node_id["id"]], dashed=node_id["id"] == "waveform_path")

            dashed_edges = {"planner_to_waveform"}
            for edge in spec["edges"]:
                add_route(ax, points_from_report(report, edge["id"]), dashed=edge["id"] in dashed_edges)

            text_report = kit.audit_plot_text(fig, min_font_pt=float(spec["min_font_pt"]))
            kit.write_json(str(args.out) + ".styled_text_report.json", text_report)
            if text_report["errors"]:
                plt.close(fig)
                print("STYLED TEXT AUDIT FAILED; no styled export written.", file=sys.stderr)
                for error in text_report["errors"]:
                    print("  " + error, file=sys.stderr)
                return 2

            report["visual_review"] = "PENDING: inspect styled PDF, SVG, PNG, and grayscale preview"
            report["scientific_review"] = "PENDING: compare semantic specification against method/source"
            kit.write_json(str(args.out) + ".geometry.json", report)
            manifest = kit.export_figure(
                fig,
                args.out,
                inputs=[args.spec, args.layout, Path(__file__), BUILDER_SCRIPTS / "render_schematic.py", BUILDER_SCRIPTS / "figurekit.py"],
                metadata={
                    "semantic_status": "User-authored reviewed example/spec; scientific scope checked against local VoxReason documentation",
                    "geometry_report": str(args.out) + ".geometry.json",
                    "styled_text_report": str(args.out) + ".styled_text_report.json",
                    "checker_note": "Bundled geometry checker used; synthetic FancyArrowPatch CLOSEPOLY ignored only for arrow/text intersection test",
                },
            )
            manifest["visual_review"] = "PENDING: independent manual inspection required"
            manifest["scientific_review"] = "PENDING: local bounded semantic review recorded separately"
            kit.write_json(str(args.out) + ".manifest.json", manifest)
            plt.close(fig)
    finally:
        MplPath.intersects_bbox = original_intersects

    print(f"GEOMETRY PASS ({len(report['warnings'])} warnings); styled text audit PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
