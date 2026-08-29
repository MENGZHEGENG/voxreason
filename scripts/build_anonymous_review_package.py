#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "dist" / "voxreason-anonymous-review.zip"
EXCLUDE_PREFIXES = (
    ".git/",
    ".pytest_cache/",
    "__pycache__/",
    "dist/",
    "outputs/",
    "paper/build/",
    "paper/tables/",
    "paper/figures/",
    "data/results/public_summary.json",
    "data/results/source_label_construct_validity.json",
    "data/results/source_label_acoustic_anchor.json",
)
REDACTIONS = {
    "https://github.com/MENGZHEGENG/voxreason": "ANONYMOUS_REPOSITORY_URL",
    "MENGZHEGENG": "ANONYMOUS_AUTHOR",
    "Mengzhe Geng": "Anonymous Authors",
    "gengm": "anonymous_user",
}
TEXT_SUFFIXES = {".bib", ".cff", ".json", ".jsonl", ".md", ".py", ".sha256", ".sty", ".tex", ".toml", ".txt"}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def include_path(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in EXCLUDE_PREFIXES)


def redacted_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix not in TEXT_SUFFIXES:
        return raw
    text = raw.decode("utf-8", errors="replace")
    for old, new in REDACTIONS.items():
        text = text.replace(old, new)
    return text.encode("utf-8")


def build_package(out_path: Path) -> list[str]:
    selected = [path for path in tracked_files() if include_path(path)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=out_path.name, suffix=".tmp", dir=out_path.parent, delete=False) as handle:
        tmp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for rel in selected:
                archive.writestr(f"voxreason-anonymous-review/{rel}", redacted_bytes(ROOT / rel))
        tmp_path.replace(out_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an anonymous review package from tracked public files.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    selected = build_package(args.out)
    print(f"wrote {args.out}")
    print(f"files {len(selected)}")


if __name__ == "__main__":
    main()
