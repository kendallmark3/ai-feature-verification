"""The verification plan: the versioned contract of AC -> checks -> evidence.

plan.json is the source of truth (Claude fills it in; people review it).
VERIFICATION_PLAN.md is rendered from it for humans and PR review.
"""
from __future__ import annotations

from pathlib import Path

from .story import load as load_story
from .util import VerifyError, now_iso, out_dir, read_json, write_json, write_text

DISPOSITIONS = {"verify", "not-verifiable", "out-of-scope"}


def init(cfg: dict, key: str, force: bool = False) -> Path:
    story = load_story(cfg, key)
    path = out_dir(cfg, key) / "plan.json"
    if path.exists() and not force:
        raise VerifyError(f"{path} exists. Edit it, or use --force to start over.")
    plan = {
        "story": key,
        "summary": story.get("summary", ""),
        "created": now_iso(),
        "tagging": f"Every test that verifies a criterion names it in its title, e.g. '{key} AC-1 ...'",
        "acs": [
            {
                "id": ac["id"],
                "text": ac["text"],
                "clarified_as": "",
                "disposition": "verify",
                "reason": "",
                "checks": [],
            }
            for ac in story.get("acceptance_criteria", [])
        ],
    }
    write_json(path, plan)
    return path


def load(cfg: dict, key: str) -> dict:
    return read_json(out_dir(cfg, key) / "plan.json")


def _open_by_ac(cfg: dict, key: str) -> dict:
    from .gaps import status  # local import: gaps imports story, as plan does
    return (status(cfg, key) or {}).get("open_by_ac", {})


def validate(cfg: dict, key: str) -> list[str]:
    plan = load(cfg, key)
    story = load_story(cfg, key)
    suites = cfg.get("suites", {})
    unresolved = _open_by_ac(cfg, key)
    problems: list[str] = []
    planned = {a["id"] for a in plan.get("acs", [])}
    for ac in story.get("acceptance_criteria", []):
        if ac["id"] not in planned:
            problems.append(f"{ac['id']} is in the story but not in the plan.")
    for ac in plan.get("acs", []):
        d = ac.get("disposition")
        if d not in DISPOSITIONS:
            problems.append(f"{ac['id']}: disposition must be one of {sorted(DISPOSITIONS)}.")
            continue
        if d == "verify":
            # An AC waiting on a Gate 1 answer may have no checks yet: expected behaviour is not invented.
            # It is reported UNRESOLVED instead, which already keeps the verdict from VERIFIED.
            if not ac.get("checks") and ac["id"] not in unresolved:
                problems.append(f"{ac['id']}: needs at least one check, or a disposition with a reason.")
            for c in ac.get("checks", []):
                if c.get("suite") not in suites:
                    problems.append(f"{ac['id']}/{c.get('id')}: suite '{c.get('suite')}' is not in verify.config.json.")
                if not c.get("description"):
                    problems.append(f"{ac['id']}/{c.get('id')}: check needs a description.")
                if not c.get("expected_evidence"):
                    problems.append(f"{ac['id']}/{c.get('id')}: say what evidence proves it (expected_evidence).")
        elif not ac.get("reason"):
            problems.append(f"{ac['id']}: '{d}' needs a reason a reviewer can accept.")
    return problems


def render(cfg: dict, key: str) -> Path:
    plan = load(cfg, key)
    problems = validate(cfg, key)
    from .gaps import status
    gate1 = status(cfg, key)
    if gate1 is None:
        g1 = "not run"
    elif gate1["passed"]:
        g1 = "all questions answered"
    else:
        aff = ", ".join(f"{ac} ({', '.join(q)})" for ac, q in gate1["open_by_ac"].items()) or "none"
        g1 = (f"{len(gate1['open'])} open question(s). Unresolved criteria: {aff}. "
              "Testing continues for every other criterion.")
    L = [
        f"# Verification Plan · {key}",
        "",
        f"**Story:** {plan.get('summary', '')}",
        "",
        f"**Gate 1 (clarifications):** {g1}",
        "",
        f"**Tagging rule:** {plan.get('tagging', '')}",
        "",
        "| AC | Criterion (as written) | Clarified as | Disposition | Checks |",
        "|---|---|---|---|---|",
    ]
    for ac in plan["acs"]:
        checks = "<br>".join(
            f"`{c.get('id', '')}` [{c.get('suite')}] {c.get('description', '')}" for c in ac.get("checks", [])
        ) or (ac.get("reason") or "—")
        L.append(
            f"| {ac['id']} | {ac['text']} | {ac.get('clarified_as') or '—'} | {ac['disposition']} | {checks} |"
        )
    L += ["", "## Expected evidence", ""]
    for ac in plan["acs"]:
        for c in ac.get("checks", []):
            L.append(f"- `{c.get('id')}`: {', '.join(c.get('expected_evidence', []))}")
    if problems:
        L += ["", "## Plan problems (must be fixed before running)", ""] + [f"- {p}" for p in problems]
    L.append("")
    return write_text(out_dir(cfg, key) / "VERIFICATION_PLAN.md", "\n".join(L))
