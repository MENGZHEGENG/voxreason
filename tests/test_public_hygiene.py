from __future__ import annotations

from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "build"}
TEXT_SUFFIXES = {
    ".bib",
    ".bst",
    ".cff",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sha256",
    ".sty",
    ".tex",
    ".toml",
    ".txt",
}
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
    rendered_visual_dir = "paper/" + "fi" + "gures/"
    removed_visual_script = "scripts/" + "draw_" + "fi" + "gures.py"
    offenders = [
        path
        for path in tracked
        if path.startswith("paper/tables/")
        or path.startswith(rendered_visual_dir)
        or path == "data/results/public_summary.json"
        or path == removed_visual_script
    ]
    assert offenders == []


def test_public_release_has_citation_and_data_use_notes() -> None:
    assert (ROOT / "BENCHMARK.md").is_file()
    assert (ROOT / "CITATION.cff").is_file()
    assert (ROOT / "DATA_USE.md").is_file()
    assert (ROOT / "LICENSE").is_file()
    assert (ROOT / "data/benchmark/source_label/summary.json").is_file()


def test_public_paper_author_metadata_is_anonymous() -> None:
    text = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    assert "\\author{Anonymous Authors}" in text
    assert "MENGZHEGENG" not in text
    assert "github.com" not in text.lower()


def test_public_paper_citations_match_bibliography_source() -> None:
    paper = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    references = (ROOT / "paper/references.bib").read_text(encoding="utf-8")
    cited = {
        key.strip()
        for citation in re.finditer(r"\\cite\w*\{([^}]+)\}", paper)
        for key in citation.group(1).split(",")
    }
    entries = set(re.findall(r"@\w+\{([^,]+),", references))

    assert cited - entries == set()
    assert entries - cited == set()
    assert "\\bibliography{references}" in paper


def test_anonymous_review_package_redacts_repository_identity(tmp_path: Path) -> None:
    out_path = tmp_path / "voxreason-anonymous-review.zip"
    subprocess.run(
        ["python3", "scripts/build_anonymous_review_package.py", "--out", str(out_path)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert out_path.is_file()
    with zipfile.ZipFile(out_path) as archive:
        names = set(archive.namelist())
        assert "voxreason-anonymous-review/.git/config" not in names
        assert "voxreason-anonymous-review/LICENSE" in names
        citation = archive.read("voxreason-anonymous-review/CITATION.cff").decode("utf-8")
        paper = archive.read("voxreason-anonymous-review/paper/main.tex").decode("utf-8")
    assert "MENGZHEGENG" not in citation + paper
    assert "github.com/MENGZHEGENG" not in citation + paper


def test_public_paper_avoids_ambiguous_modal_claims() -> None:
    text = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    pattern = re.compile(r"\b(?:" + "ca" + "n|" + "sho" + "uld" + r")\b", re.IGNORECASE)
    offenders = []
    for match in pattern.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        offenders.append(f"paper/main.tex:{line}:{match.group(0)}")
    assert offenders == []


def test_readme_explains_paper_table_regeneration_order() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    reproduce_index = text.index("python3 scripts/reproduce_results.py")
    build_index = text.index("latexmk -pdf main.tex")
    assert reproduce_index < build_index
    assert "LaTeX tables are rebuilt locally and ignored by Git" in text
