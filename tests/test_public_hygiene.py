from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "build"}
TEXT_SUFFIXES = {
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sha256",
    ".toml",
    ".txt",
}
PUBLIC_MARKDOWN_FILES = {"README.md", "BENCHMARK.md"}
FORBIDDEN_WORDS = [
    "arti" + "fact",
    "arti" + "facts",
    "mani" + "fest",
    "mani" + "fests",
    "slu" + "rm",
    "syn" + "thia",
    "sba" + "tch",
    "squ" + "eue",
    "sac" + "ct",
    "sr" + "un",
    "mo" + "s",
    "natural" + "ness",
    "human" + "-preference",
    "listener" + "-perceived",
    "deployment" + "-readiness",
    "generated" + "-audio",
    "generated" + "-speech quality",
    "ic" + "lr",
    "open" + "review",
]
FORBIDDEN = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in FORBIDDEN_WORDS) + r")\b|" + re.escape("/scr" + "atch/"),
    re.IGNORECASE,
)


def iter_public_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix in TEXT_SUFFIXES:
            files.append(path)
    return files


def test_public_text_has_no_local_or_banned_terms() -> None:
    offenders: list[str] = []
    for path in iter_public_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in FORBIDDEN.finditer(text):
            rel = path.relative_to(ROOT)
            line = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{rel}:{line}:{match.group(0)}")
    assert offenders == []


def test_public_markdown_avoids_report_table_wording() -> None:
    pattern = re.compile(r"\brows?\b", re.IGNORECASE)
    offenders: list[str] = []
    for name in PUBLIC_MARKDOWN_FILES:
        path = ROOT / name
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{name}:{line}:{match.group(0)}")
    assert offenders == []


def test_no_cluster_launch_files_are_present() -> None:
    disallowed_suffixes = {"." + "sba" + "tch", "." + "slu" + "rm"}
    disallowed_names = {"submit.sh", "launch.sh", "run_cluster.sh"}
    offenders = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)
        and (path.suffix in disallowed_suffixes or path.name in disallowed_names)
    ]
    assert offenders == []


def test_public_file_names_are_venue_neutral() -> None:
    forbidden = re.compile(r"ic" + "lr|open" + "review", re.IGNORECASE)
    offenders = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if not any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)
        and forbidden.search(str(path.relative_to(ROOT)))
    ]
    assert offenders == []


def test_generated_paper_outputs_are_not_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.splitlines()
    rendered_visual_dir = "pa" + "per/" + "fi" + "gures/"
    rendered_table_dir = "pa" + "per/tables/"
    removed_visual_script = "scripts/" + "draw_" + "fi" + "gures.py"
    offenders = [
        path
        for path in tracked
        if path.startswith(rendered_table_dir)
        or path.startswith(rendered_visual_dir)
        or path == "data/results/public_summary.json"
        or path == removed_visual_script
    ]
    assert offenders == []


def test_public_release_has_core_reproduction_files() -> None:
    assert (ROOT / "BENCHMARK.md").is_file()
    assert (ROOT / "LICENSE").is_file()
    assert (ROOT / "data/benchmark/source_label/summary.json").is_file()


def test_readme_keeps_fast_verification_commands() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Fast Verification" in text
    assert "python3 scripts/check_benchmark_files.py" in text
    assert "python3 scripts/reproduce_results.py" in text
    assert "python3 -m pytest tests/test_reproduce_results.py tests/test_public_hygiene.py" in text


def test_public_release_excludes_manuscript_source_files() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.splitlines()
    manuscript_source_dir = "pa" + "per/"
    citation_file = "CITA" + "TION.cff"
    data_use_file = "DATA" + "_USE.md"
    offenders = [path for path in tracked if path.startswith(manuscript_source_dir) or path in {citation_file, data_use_file}]
    assert offenders == []
