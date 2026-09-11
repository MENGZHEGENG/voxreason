#!/usr/bin/env python3
"""Run the bundled schematic renderer with a local arrow-path correction.

Matplotlib's FancyArrowPatch adds a CLOSEPOLY vertex at (0, 0) to the
rendered arrow path. The bundled checker treats that synthetic closure as a
real segment when testing arrow/text intersections, producing false positives
through unrelated lower nodes. This wrapper removes only the synthetic
closure for that intersection test; all route, node, text, port, and crossing
checks remain active.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from matplotlib.path import Path as MplPath

BUILDER_SCRIPTS = Path("/Users/gengm/.codex/skills/academic-figure-builder/scripts")
sys.path.insert(0, str(BUILDER_SCRIPTS))
import render_schematic as bundled  # noqa: E402


def corrected_intersects_bbox(self, bbox, filled=False):
    """Ignore FancyArrowPatch's synthetic CLOSEPOLY-to-origin segment."""
    if self.codes is not None and len(self.codes) >= 2 and self.codes[-1] == MplPath.CLOSEPOLY:
        open_codes = self.codes[:-1]
        open_vertices = self.vertices[:-1]
        return MplPath(open_vertices, open_codes).intersects_bbox(bbox, filled=filled)
    return _ORIGINAL_INTERSECTS_BBOX(self, bbox, filled=filled)


_ORIGINAL_INTERSECTS_BBOX = MplPath.intersects_bbox


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Output stem without extension")
    parser.add_argument("--force", action="store_true", help="Overwrite named outputs")
    args = parser.parse_args()

    bundled.reserve_outputs(
        args.out,
        (".pdf", ".svg", ".png", ".manifest.json", ".geometry.json", "_DRAFT.png"),
        args.force,
    )
    spec, layout = bundled.read_json(args.spec), bundled.read_json(args.layout)
    MplPath.intersects_bbox = corrected_intersects_bbox
    try:
        with bundled.publication_style(float(spec.get("font_pt", 9))):
            fig, report = bundled.construct(spec, layout)
            bundled.write_json(str(args.out) + ".geometry.json", report)
            if report["errors"]:
                fig.savefig(str(args.out) + "_DRAFT.png", dpi=160, bbox_inches=None)
                bundled.write_json(
                    str(args.out) + ".manifest.json",
                    {"status": "FAILED_NO_CURRENT_EXPORT", "errors": report["errors"]},
                )
                bundled.plt.close(fig)
                print("GEOMETRY FAILED; only an explicitly named draft preview was exported.", file=sys.stderr)
                for error in report["errors"]:
                    print("  " + error, file=sys.stderr)
                return 2
            bundled.export_figure(
                fig,
                args.out,
                inputs=[
                    args.spec,
                    args.layout,
                    Path(__file__),
                    BUILDER_SCRIPTS / "render_schematic.py",
                    BUILDER_SCRIPTS / "figurekit.py",
                ],
                metadata={
                    "semantic_status": "User-authored example/spec; not scientifically verified",
                    "geometry_report": str(args.out) + ".geometry.json",
                    "checker_note": "Synthetic FancyArrowPatch CLOSEPOLY ignored only for arrow/text intersection test",
                },
            )
            bundled.plt.close(fig)
    finally:
        MplPath.intersects_bbox = _ORIGINAL_INTERSECTS_BBOX
    print(f"GEOMETRY PASS ({len(report['warnings'])} warnings). Scientific and visual review remain pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
