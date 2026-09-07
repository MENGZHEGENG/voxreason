#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voxreason_public.benchmark import load_split_cases, validate_cases  # noqa: E402


def main() -> None:
    cases = load_split_cases(ROOT)
    report = validate_cases(cases)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["issue_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
