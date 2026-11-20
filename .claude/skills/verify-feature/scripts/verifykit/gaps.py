"""Gate 1: deterministic gap analysis of a story's acceptance criteria.

The rules are plain pattern checks, so the same story always yields the same
questions. Claude adds judgement-based questions in the same file format
(IDs starting Q-AI-).

Clarification is exception-based: open questions do not stop testing. Each
open question marks only the criteria it names as UNRESOLVED (never PASS), and
is recorded with the person who owns the answer. Gate 1 "passes" when every
question has an Answer; an unanswered question is never treated as approval.
"""
from __future__ import annotations

import re
from pathlib import Path

from .story import load as load_story
from .util import VerifyError, out_dir, write_json, write_text

VAGUE = [
    "fast", "quick", "quickly", "slow", "easy", "easily", "simple", "user-friendly", "user friendly",
    "intuitive", "properly", "correctly", "appropriate", "appropriately", "seamless", "seamlessly",
    "robust", "nice", "good", "better", "etc", "as needed", "if possible", "should work", "works",
    "reasonable", "normal", "standard",
]
NFR = ["fast", "quick", "quickly", "slow", "performance", "performant", "latency", "responsive", "scalable", "load"]
MEASURE = re.compile(r"\d+(\.\d+)?\s*(ms|milliseconds?|s|sec|seconds?|%|percent|rps|req/s|users?|p\d{2})\b", re.I)
UNDEFINED = ["valid", "invalid", "correct", "incorrect", "supported", "allowed", "eligible", "right"]
ENV_WORDS = ["mobile", "phone", "tablet", "browser", "browsers", "device", "devices", "desktop", "responsive"]
ENV_SPECIFIC = re.compile(r"\b(ios|android|safari|chrome|firefox|edge|\d{3,4}\s*px|viewport|breakpoint|iphone|pixel)\b", re.I)
OBSERVABLE = re.compile(
    r"\b(show|shows|shown|display|displays|displayed|see|sees|return|returns|respond|responds|apply|applies|applied|"
    r"receive|receives|appear|appears|redirect|redirects|save|saves|saved|store|stores|send|sends|sent|reject|rejects|"
    r"rejected|accept|accepts|accepted|update|updates|updated|error|message|status|total|enter|enters|"
    r"click|clicks|log|logs|emit|emits|visible)\b",
    re.I,
)
ERROR_PATH = re.compile(r"\b(error|invalid|fail|fails|failure|reject|declin|not\b|cannot|can't|expired|denied)\w*", re.I)
EXAMPLE = re.compile(r"(\d|\"[^\"]+\"|'[^']+'|`[^`]+`|e\.g\.|for example|such as)", re.I)


def _has_word(text: str, word: str) -> bool:
    return re.search(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text, re.I) is not None


def analyse(story: dict) -> list[dict]:
    findings: list[dict] = []

    def add(ac, rule, quote, question):
        findings.append({"ac": ac, "rule": rule, "quote": quote, "question": question})

    acs = story.get("acceptance_criteria", [])
    for ac in acs:
        t = ac["text"]
        vague = [w for w in VAGUE if _has_word(t, w)]
        nfr = [w for w in NFR if _has_word(t, w)]
        if nfr and not MEASURE.search(t):
            add(ac["id"], "UNMEASURED_NFR", t,
                f"'{nfr[0]}' has no number. What threshold, measured where (API, page load, click-to-result), "
                "at what percentile, under what load?")
            vague = [w for w in vague if w not in nfr]
        if vague:
            add(ac["id"], "VAGUE_TERM", t,
                f"'{vague[0]}' can't be tested as written. What exact, observable result counts as passing?")
        und = [w for w in UNDEFINED if _has_word(t, w)]
        if und and not EXAMPLE.search(t):
            add(ac["id"], "UNDEFINED_RULE", t,
                f"What makes something '{und[0]}'? List the rules or give concrete examples of each case.")
        env = [w for w in ENV_WORDS if _has_word(t, w)]
        if env and not ENV_SPECIFIC.search(t):
            add(ac["id"], "UNSPECIFIED_ENVIRONMENT", t,
                f"'{env[0]}' — which devices, browsers or viewport widths must pass?")
        already_flagged = any(f["ac"] == ac["id"] for f in findings)
        if not OBSERVABLE.search(t) and not already_flagged:
            add(ac["id"], "NO_OBSERVABLE_OUTCOME", t,
                "What does the user or caller observe when this is met (a message, a value, a status)?")

    all_text = " ".join(a["text"] for a in acs)
    if not acs:
        add("STORY", "NO_ACCEPTANCE_CRITERIA", story.get("summary", ""),
            "There are no acceptance criteria. What must be true for this story to be done?")
    else:
        if len(acs) < 2:
            add("STORY", "TOO_FEW_CRITERIA", all_text, "Only one criterion. Are error and edge cases out of scope?")
        if not ERROR_PATH.search(all_text):
            add("STORY", "NO_ERROR_PATH", "", "No criterion covers a failure case. What should happen when it goes wrong?")
        if not EXAMPLE.search(all_text):
            add("STORY", "NO_EXAMPLES", "", "No criterion has a concrete value or example. Can you give at least one worked example?")
    if not story.get("description", "").strip():
        add("STORY", "NO_DESCRIPTION", "", "The story has no description. Who is this for and why?")

    for i, f in enumerate(findings, 1):
        f["id"] = f"Q-{i}"
    return findings


def owner_of(story: dict) -> str:
    """Who answers requirement questions: the story's reporter when known."""
    return (story.get("reporter") or "").strip() or "Product owner (not named on the story)"


def _render(story: dict, findings: list[dict]) -> str:
    owner = owner_of(story)
    lines = [
        f"# Gate 1 · Clarifications for {story['key']}",
        "",
        f"**Story:** {story.get('summary', '')}",
        "",
        "Testing does not wait for these answers. Each open question marks only the criterion it",
        "names as UNRESOLVED: its tests may still run, but it can never be reported as passing until",
        "the owner answers. An answer can be a decision, a rule, an example, or `Accepted risk: <why>`.",
        "Questions from the deterministic rules come first; Claude adds judgement questions below",
        "them with IDs `Q-AI-n`.",
        "",
        "Check with: `python3 .claude/skills/verify-feature/scripts/verify.py gate1 " + story["key"] + " --check`",
        "",
    ]
    for f in findings:
        lines += [f"## {f['id']} · {f['ac']} · {f['rule']}", ""]
        if f["quote"]:
            lines += [f"> {f['quote']}", ""]
        lines += [f"Owner: {owner}", "", f"Question: {f['question']}", "", "Answer: ", ""]
    lines += ["<!-- Claude: add judgement questions below this line as ## Q-AI-n · AC-x · TOPIC -->", ""]
    return "\n".join(lines)


def run(cfg: dict, key: str, force: bool = False) -> tuple[Path, list[dict]]:
    story = load_story(cfg, key)
    findings = analyse(story)
    d = out_dir(cfg, key)
    md = d / "gate1-clarifications.md"
    if md.exists() and not force:
        raise VerifyError(f"{md} exists and may hold answers. Use --force to overwrite.")
    write_text(md, _render(story, findings))
    write_json(d / "gate1-findings.json", findings)
    return md, findings


_Q = re.compile(r"^##\s+(Q-[\w-]+)\s*·?(.*)$")
_AC = re.compile(r"\bAC-\d+\b")


def parse(text: str) -> list[dict]:
    """Questions in a Gate 1 file: id, the ACs its heading names, owner, answer."""
    questions, current = [], None
    for line in text.splitlines():
        m = _Q.match(line)
        if m:
            heading = m.group(2).strip(" ·")
            scope = heading.split("·")[0] if "·" in heading else heading
            current = {"id": m.group(1), "heading": heading, "acs": sorted(set(_AC.findall(scope)), key=_ac_num),
                       "owner": "", "answer": ""}
            questions.append(current)
        elif current is not None and line.lower().startswith("answer:"):
            current["answer"] = line.split(":", 1)[1].strip()
        elif current is not None and line.lower().startswith("owner:"):
            current["owner"] = line.split(":", 1)[1].strip()
    return questions


def _ac_num(ac: str) -> int:
    return int(ac.split("-")[1])


def check(cfg: dict, key: str) -> dict:
    md = out_dir(cfg, key) / "gate1-clarifications.md"
    if not md.is_file():
        raise VerifyError(f"No Gate 1 file yet. Run: verify.py gaps {key}")
    questions = parse(md.read_text(encoding="utf-8"))
    try:
        default_owner = owner_of(load_story(cfg, key))
    except VerifyError:
        default_owner = owner_of({})
    open_q = [q for q in questions if not q["answer"]]
    open_by_ac: dict[str, list[str]] = {}
    for q in open_q:
        for ac in q["acs"]:
            open_by_ac.setdefault(ac, []).append(q["id"])
    result = {
        "questions": len(questions), "answered": len(questions) - len(open_q),
        "open": [q["id"] for q in open_q], "passed": not open_q,
        # Exception-based clarification: which criteria each open question leaves unresolved.
        "open_by_ac": dict(sorted(open_by_ac.items(), key=lambda kv: _ac_num(kv[0]))),
        "story_level_open": [q["id"] for q in open_q if not q["acs"]],
        "open_detail": [{"id": q["id"], "acs": q["acs"], "topic": q["heading"],
                         "owner": q["owner"] or default_owner} for q in open_q],
    }
    write_json(out_dir(cfg, key) / "gate1-status.json", result)
    return result


def status(cfg: dict, key: str) -> dict | None:
    """Current Gate 1 state, re-read from the file so edits are never stale. None if there is no Gate 1 file."""
    if not (out_dir(cfg, key) / "gate1-clarifications.md").is_file():
        return None
    return check(cfg, key)
