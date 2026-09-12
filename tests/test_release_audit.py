from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_release import audit_release_directory  # noqa: E402


def _write_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.7\nminimal test pdf\n")


def _write_zip(path: Path, members: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def _make_release(root: Path, *, kind: str = "iclr2027") -> Path:
    source = root / "source"
    source.mkdir(parents=True)
    tex_name = "voxreason_iclr2027.tex" if kind == "iclr2027" else "voxreason_arxiv.tex"
    tex = r"""\documentclass{article}
\usepackage{graphicx}
\begin{document}
\title{VoxReason}
CONTENT
\end{document}
"""
    if kind == "arxiv":
        tex = tex.replace("\\title{VoxReason}", "\\iclrfinalcopy\n\\author{Mengzhe Geng}\n\\title{VoxReason}")
    (source / tex_name).write_text(tex, encoding="utf-8")
    (source / "iclr2027_conference.sty").write_text("% local style\n", encoding="utf-8")
    (source / "math_commands.tex").write_text("% local math\n", encoding="utf-8")
    (source / "figures").mkdir()
    (source / "figures" / "core.pdf").write_bytes(b"%PDF-1.7\nfigure\n")
    (source / "tables").mkdir()
    (source / "tables" / "results.tex").write_text("% table\n", encoding="utf-8")
    _write_pdf(root / "paper.pdf")
    _write_zip(root / "source.zip", {f"source/{tex_name}": tex})
    return root


def test_clean_anonymous_release_directory_passes(tmp_path: Path) -> None:
    release = _make_release(tmp_path / "iclr2027")

    assert audit_release_directory(release, "iclr2027") == []


def test_anonymous_release_rejects_author_identity(tmp_path: Path) -> None:
    release = _make_release(tmp_path / "iclr2027")
    tex = next((release / "source").glob("*.tex"))
    tex.write_text(tex.read_text(encoding="utf-8") + "\\author{Mengzhe Geng}\n", encoding="utf-8")

    issues = audit_release_directory(release, "iclr2027")

    assert any("author identity" in issue for issue in issues)


def test_release_rejects_private_audio_and_legacy_paths(tmp_path: Path) -> None:
    release = _make_release(tmp_path / "arxiv", kind="arxiv")
    private = release / "source" / "runs" / "legacy"
    private.mkdir(parents=True)
    (private / "sample.wav").write_bytes(b"audio")

    issues = audit_release_directory(release, "arxiv")

    assert any("private or generated media" in issue for issue in issues)
    assert any("legacy or build output" in issue for issue in issues)


def test_release_rejects_unsafe_zip_member(tmp_path: Path) -> None:
    release = _make_release(tmp_path / "iclr2027")
    _write_zip(release / "source.zip", {"../../outside.txt": "unsafe"})

    issues = audit_release_directory(release, "iclr2027")

    assert any("unsafe archive member" in issue for issue in issues)


def test_unknown_release_kind_is_rejected(tmp_path: Path) -> None:
    release = _make_release(tmp_path / "iclr2027")

    with pytest.raises(ValueError, match="kind"):
        audit_release_directory(release, "camera_ready")
