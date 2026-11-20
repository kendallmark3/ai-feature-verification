"""Pull a story and normalise its acceptance criteria into stable AC IDs."""
from __future__ import annotations

import re

from . import jira
from .util import VerifyError, now_iso, out_dir, read_json, write_json

_EXPLICIT_ID = re.compile(r"^\s*(?:[-*•]\s*)?\[?(AC-\d+)\]?\s*[:.)\-–]\s*(.+)$", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.+)$")
_AC_HEADING = re.compile(r"^\s*(?:h\d\.\s*|#+\s*)?acceptance criteria\s*:?\s*$", re.I)


def _lines_from(value) -> list[str]:
    if isinstance(value, list):
        # Each list item is one criterion: give plain items a bullet so they are not joined.
        return [str(v) if (_EXPLICIT_ID.match(str(v)) or _BULLET.match(str(v))) else f"- {v}" for v in value]
    return str(value or "").splitlines()


def _ac_block_from_description(desc: str) -> list[str]:
    """Fallback: take the list under an 'Acceptance Criteria' heading."""
    out, inside = [], False
    for line in desc.splitlines():
        if _AC_HEADING.match(line):
            inside = True
            continue
        if inside:
            if re.match(r"^\s*(?:h\d\.|#+)\s*\S", line):
                break
            out.append(line)
    return out


def parse_acceptance_criteria(raw_lines: list[str]) -> list[dict]:
    """Return [{'id': 'AC-1', 'text': ...}] in source order.

    Explicit IDs ("AC-3: ...") are kept. Otherwise each bullet or numbered line
    becomes the next free AC number. Continuation lines join the previous AC.
    """
    acs: list[dict] = []
    used: set[str] = set()
    for line in raw_lines:
        if not line.strip():
            continue
        m = _EXPLICIT_ID.match(line)
        if m:
            ac_id, text = m.group(1).upper(), m.group(2).strip()
        else:
            b = _BULLET.match(line)
            if b:
                ac_id, text = None, b.group(1).strip()
            elif acs:
                acs[-1]["text"] += " " + line.strip()
                continue
            else:
                ac_id, text = None, line.strip()
        acs.append({"id": ac_id, "text": text})
        if ac_id:
            used.add(ac_id)
    n = 0
    for ac in acs:
        if ac["id"] is None:
            n += 1
            while f"AC-{n}" in used:
                n += 1
            ac["id"] = f"AC-{n}"
            used.add(ac["id"])
    return acs


def pull(cfg: dict, key: str) -> dict:
    issue = jira.adapter(cfg).get_issue(key)
    lines = _lines_from(issue.get("acceptance_criteria"))
    if not any(l.strip() for l in lines):
        lines = _ac_block_from_description(issue.get("description", ""))
    acs = parse_acceptance_criteria(lines)
    story = {
        "key": issue.get("key", key),
        "summary": issue.get("summary", ""),
        "type": issue.get("type", ""),
        "status": issue.get("status", ""),
        "description": issue.get("description", ""),
        "acceptance_criteria": acs,
        "pulled_at": now_iso(),
    }
    if not acs:
        story["warning"] = "No acceptance criteria found. Gate 1 will flag this."
    write_json(out_dir(cfg, key) / "story.json", story)
    return story


def load(cfg: dict, key: str) -> dict:
    path = out_dir(cfg, key) / "story.json"
    if not path.is_file():
        raise VerifyError(f"Story not pulled yet. Run: verify.py story {key}")
    return read_json(path)
