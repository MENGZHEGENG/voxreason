#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voxreason_public.benchmark import load_split_cases, validate_cases  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checksums(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(maxsplit=1)
        rows[rel] = digest
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate VoxReasonBench public files and checksums.")
    parser.add_argument("--checksums", default="data/benchmark/source_label/checksums.sha256")
    args = parser.parse_args()

    checksum_path = ROOT / args.checksums
    expected = read_checksums(checksum_path)
    mismatches: list[dict[str, str]] = []
    for rel, digest in sorted(expected.items()):
        path = ROOT / rel
        if not path.is_file():
            mismatches.append({"path": rel, "status": "missing"})
            continue
        observed = sha256(path)
        if observed != digest:
            mismatches.append({"path": rel, "status": "mismatch", "expected": digest, "observed": observed})

    case_report = validate_cases(load_split_cases(ROOT))
    report = {
        "checked_files": len(expected),
        "case_count": case_report["case_count"],
        "case_issue_count": case_report["issue_count"],
        "checksum_mismatches": mismatches,
        "ready": not mismatches and case_report["issue_count"] == 0,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
