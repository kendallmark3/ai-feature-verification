"""Gate 2: list AI-proposed tests and record a person's promotion of them."""
from __future__ import annotations

import re
from pathlib import Path

from .util import VerifyError, now_iso, out_dir, read_json, today, write_json

MARKER = re.compile(r"@ai-proposed\b")


def proposed(cfg: dict) -> list[str]:
    from .report import unpromoted_in_suites  # same scope as the verdict uses
    return unpromoted_in_suites(cfg)


def promote(cfg: dict, file: str, by: str, story: str | None) -> dict:
    root = Path(cfg["_root"])
    path = (root / file).resolve()
    if not path.is_file() or root.resolve() not in path.parents:
        raise VerifyError(f"{file} is not a file inside the repository.")
    text = path.read_text(encoding="utf-8")
    if not MARKER.search(text):
        raise VerifyError(f"{file} has no @ai-proposed marker.")
    if not by.strip():
        raise VerifyError("--by must name the person approving.")
    new, n = MARKER.subn(f"@approved-by {by} {today()}", text)
    path.write_text(new, encoding="utf-8")
    record = {"file": file, "by": by, "at": now_iso(), "markers": n}
    if story:
        log_path = out_dir(cfg, story) / "gate2-promotions.json"
        log = read_json(log_path, default=[])
        log.append(record)
        write_json(log_path, log)
    return record
