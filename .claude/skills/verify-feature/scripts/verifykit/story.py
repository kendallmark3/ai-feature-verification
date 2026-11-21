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


_WIKI_HEADING = re.compile(r"^\s*h\d\.\s*\S")
_MD_HEADING = re.compile(r"^\s*#+\s+\S")
_WIKI_ITEM = re.compile(r"^\s*[#*]+\s+(.+)$")


def _ac_block_from_description(desc: str) -> list[str]:
    """Fallback: take the list under an 'Acceptance Criteria' heading.

    Handles both Markdown ("## Acceptance Criteria" + "1. item") and the Jira wiki markup
    that REST API v2 returns ("h2. Acceptance Criteria" + "# item" or "* item"). In wiki
    markup "#" starts a numbered item, not a heading, so the style is taken from the heading.
    """
    out, inside, wiki = [], False, False
    for line in desc.splitlines():
        if not inside and _AC_HEADING.match(line):
            inside, wiki = True, bool(_WIKI_HEADING.match(line))
            continue
        if inside:
            if _WIKI_HEADING.match(line) or (not wiki and _MD_HEADING.match(line)):
                break
            item = _WIKI_ITEM.match(line) if wiki else None
            out.append(f"- {item.group(1).strip()}" if item else line)
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
        "reporter": issue.get("reporter", ""),  # owner of requirement questions at Gate 1
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


def require_criteria(cfg: dict, key: str) -> list[dict]:
    """Refuse to go on when the pulled story has no acceptance criteria."""
    acs = load(cfg, key).get("acceptance_criteria", [])
    if not acs:
        raise VerifyError(
            f"{key} has no acceptance criteria, so no tests are run. Add them to the story in Jira "
            f"(a numbered list under an 'Acceptance Criteria' heading in the description), "
            f"then run: verify.py story {key}"
        )
    return acs
