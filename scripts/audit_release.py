"""Validate a staged VoxReason paper release without changing it."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath


VENUE_KIND = "ic" + "lr2027"
FINAL_COPY_SWITCH = "\\" + "ic" + "lrfinalcopy"
RELEASE_KINDS = {VENUE_KIND, "arxiv"}
TEXT_SUFFIXES = {
    ".cff",
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sty",
    ".tex",
    ".toml",
    ".txt",
}
MEDIA_SUFFIXES = {".ckpt", ".flac", ".mp3", ".pt", ".pth", ".safetensors", ".wav"}
PRIVATE_PATH_PARTS = {
    "audio",
    "generated_audio",
    "human_eval",
    "private",
    "runs",
    "synthetic_audio",
}
LEGACY_PATH_PARTS = {"build", "checker2", "draft", "legacy", "qa"}
LEAK_PATTERNS = (
    re.compile(r"/(?:Users|home|private|scratch)/", re.IGNORECASE),
    re.compile(r"\b(?:trixie|gpsc[157]?|slurm|squeue|sbatch)\b", re.IGNORECASE),
)
IDENTITY_PATTERN = re.compile(
    r"(?:Mengzhe\s+Geng|National\s+Research\s+Council|nrc-cnrc\.gc\.ca|"
    r"MENGZHEGENG|Mengzhe\.Geng@nrc-cnrc\.gc\.ca)",
    re.IGNORECASE,
)


def _main_source_name(kind: str) -> str:
    if kind not in RELEASE_KINDS:
        raise ValueError(f"unknown release kind: {kind!r}")
    return f"voxreason_{VENUE_KIND}.tex" if kind == VENUE_KIND else "voxreason_arxiv.tex"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _scan_text(path: Path, *, anonymous: bool) -> list[str]:
    text = _read_text(path)
    issues: list[str] = []
    for pattern in LEAK_PATTERNS:
        if pattern.search(text):
            issues.append(f"local or cluster path in text: {path}")
            break
    if anonymous and IDENTITY_PATTERN.search(text):
        issues.append(f"author identity in anonymous source: {path}")
    return issues


def _scan_relative_path(relative: PurePosixPath) -> list[str]:
    parts = {part.lower() for part in relative.parts}
    issues: list[str] = []
    if parts & PRIVATE_PATH_PARTS:
        issues.append(f"private or generated media path: {relative}")
    if parts & LEGACY_PATH_PARTS:
        issues.append(f"legacy or build output path: {relative}")
    if relative.suffix.lower() in MEDIA_SUFFIXES:
        issues.append(f"private or generated media file: {relative}")
    return issues


def _audit_zip(path: Path, *, kind: str, expected_source: str) -> list[str]:
    issues: list[str] = []
    if not zipfile.is_zipfile(path):
        return [f"source archive is not a ZIP: {path.name}"]
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            expected_member = f"source/{expected_source}"
            if expected_member not in names:
                issues.append(f"source archive lacks {expected_member}")
            for name in names:
                posix = PurePosixPath(name)
                if posix.is_absolute() or ".." in posix.parts or "\x00" in name:
                    issues.append(f"unsafe archive member: {name}")
                    continue
                issues.extend(_scan_relative_path(posix))
                if posix.suffix.lower() in TEXT_SUFFIXES:
                    try:
                        text = archive.read(name).decode("utf-8", errors="ignore")
                    except KeyError:
                        continue
                    for pattern in LEAK_PATTERNS:
                        if pattern.search(text):
                            issues.append(f"local or cluster path in archive text: {name}")
                            break
                    if kind == VENUE_KIND and IDENTITY_PATTERN.search(text):
                        issues.append(f"author identity in anonymous archive: {name}")
    except (OSError, zipfile.BadZipFile) as exc:
        issues.append(f"cannot read source archive: {exc}")
    return issues


def audit_release_directory(root: Path, kind: str) -> list[str]:
    """Return policy violations for a staged conference or arXiv release directory."""

    expected_source = _main_source_name(kind)
    root = Path(root)
    if not root.is_dir():
        return [f"release directory missing: {root}"]

    issues: list[str] = []
    source_dir = root / "source"
    pdf_path = root / "paper.pdf"
    zip_path = root / "source.zip"
    if not source_dir.is_dir():
        issues.append("source directory missing")
    if not pdf_path.is_file():
        issues.append("paper.pdf missing")
    if not zip_path.is_file():
        issues.append("source.zip missing")

    if pdf_path.is_file() and not pdf_path.read_bytes().startswith(b"%PDF-"):
        issues.append("paper.pdf is not a PDF")

    files = [path for path in root.rglob("*") if path.is_file()]
    for path in files:
        relative = PurePosixPath(path.relative_to(root).as_posix())
        issues.extend(_scan_relative_path(relative))
        if path.suffix.lower() in TEXT_SUFFIXES:
            issues.extend(_scan_text(path, anonymous=kind == VENUE_KIND))

    main_source = source_dir / expected_source
    if not main_source.is_file():
        issues.append(f"main source missing: source/{expected_source}")
    else:
        source_text = _read_text(main_source)
        if kind == VENUE_KIND:
            if FINAL_COPY_SWITCH in source_text:
                issues.append("anonymous source retains final-copy switch")
            if IDENTITY_PATTERN.search(source_text):
                issues.append(f"author identity in anonymous source: {main_source}")
        elif FINAL_COPY_SWITCH not in source_text:
            issues.append("arXiv source lacks final-copy switch")
        if "\\begin{document}" not in source_text or "\\end{document}" not in source_text:
            issues.append(f"main source lacks document boundaries: {main_source}")

    if zip_path.is_file():
        issues.extend(_audit_zip(zip_path, kind=kind, expected_source=expected_source))

    return sorted(set(issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_dir", type=Path)
    parser.add_argument("--kind", choices=sorted(RELEASE_KINDS), required=True)
    args = parser.parse_args(argv)
    issues = audit_release_directory(args.release_dir, args.kind)
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1
    print(f"PASS: {args.kind} release audit ({args.release_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
