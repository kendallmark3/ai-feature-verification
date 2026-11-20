"""Verification report, Jira comment, and the human approval record (Gate 3)."""
from __future__ import annotations

from pathlib import Path

from . import jira
from .inspect_repo import scan_tests
from .plan import validate as validate_plan
from .util import VerifyError, now_iso, out_dir, read_json, write_json, write_text

ICON = {"pass": "PASS", "fail": "FAIL", "missing": "NOT COVERED", "not-verifiable": "NOT VERIFIABLE",
        "out-of-scope": "OUT OF SCOPE"}


def verdict(ev: dict, gate1_passed: bool, plan_problems: list[str], proposed: list[str]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    failing = [c["id"] for c in ev["coverage"] if c["status"] == "fail"]
    suite_errors = [n for n, s in ev["suites"].items() if s["error"]]
    if failing:
        reasons.append(f"Failing criteria: {', '.join(failing)}")
    if ev["regression"]["failed"]:
        reasons.append(f"{len(ev['regression']['failed'])} existing regression test(s) failing")
    if suite_errors:
        reasons.append(f"Suite(s) errored without results: {', '.join(suite_errors)}")
    if reasons:
        return "NOT VERIFIED", reasons
    missing = [c["id"] for c in ev["coverage"] if c["status"] == "missing"]
    unverifiable = [c["id"] for c in ev["coverage"] if c["status"] == "not-verifiable"]
    if not gate1_passed:
        reasons.append("Gate 1 has unanswered clarification questions")
    if plan_problems:
        reasons.append(f"Plan has {len(plan_problems)} problem(s)")
    if missing:
        reasons.append(f"No passing evidence for: {', '.join(missing)}")
    if unverifiable:
        reasons.append(f"Not verifiable as written: {', '.join(unverifiable)}")
    if proposed:
        reasons.append(f"{len(proposed)} test file(s) still @ai-proposed (Gate 2 open)")
    if ev["mode"] != "pipeline":
        reasons.append("Evidence is from interactive mode; re-run in pipeline mode before approval")
    if reasons:
        return "INCOMPLETE", reasons
    return "VERIFIED", ["Every in-scope criterion has passing, traced evidence"]


def build(cfg: dict, key: str) -> dict:
    d = out_dir(cfg, key)
    ev = read_json(d / "evidence.json")
    story = read_json(d / "story.json")
    gate1 = read_json(d / "gate1-status.json", default={"passed": False, "open": ["not run"]})
    problems = validate_plan(cfg, key)
    proposed = [t["path"] for t in scan_tests(Path(cfg["_root"])) if t["ai_proposed"]]
    v, reasons = verdict(ev, gate1.get("passed", False), problems, proposed)
    rep = {
        "story": key, "summary": story.get("summary", ""), "verdict": v, "reasons": reasons,
        "generated": now_iso(), "run_id": ev["run_id"], "mode": ev["mode"], "environment": ev["environment"],
        "git_sha": ev.get("git_sha"),
        "gates": {
            "gate1_clarify": "passed" if gate1.get("passed") else "open",
            "gate2_promote": "passed" if not proposed else f"open ({len(proposed)} file(s))",
            "gate3_approve": "pending human decision",
        },
        "coverage": [
            {k: c[k] for k in ("id", "status", "text", "clarified_as", "reason")}
            | {"tests": sum(1 for t in c["tests"] if t["status"] != "skip"),
               "passed": sum(1 for t in c["tests"] if t["status"] == "pass")}
            for c in ev["coverage"]
        ],
        "regression": dict(ev["regression"]),
    }
    write_json(d / "report.json", rep)

    L = [f"# Verification Report · {key}", "", f"**{story.get('summary', '')}**", "",
         f"## Verdict: {v}", ""] + [f"- {r}" for r in reasons] + [
        "", f"Run `{ev['run_id']}` · mode **{ev['mode']}** · environment **{ev['environment']}**"
            + (f" · commit `{ev['git_sha']}`" if ev.get("git_sha") else ""),
        "", "## Gates", "",
        f"- Gate 1 · Clarify: **{rep['gates']['gate1_clarify']}**",
        f"- Gate 2 · Promote tests: **{rep['gates']['gate2_promote']}**",
        f"- Gate 3 · Human approval: **{rep['gates']['gate3_approve']}**",
        "", "## Coverage vs acceptance criteria", "",
        "| AC | Result | Criterion | Clarified as | Passed / ran |", "|---|---|---|---|---|"]
    for c in ev["coverage"]:
        passed = sum(1 for t in c["tests"] if t["status"] == "pass")
        ran = sum(1 for t in c["tests"] if t["status"] != "skip")
        L.append(f"| {c['id']} | **{ICON[c['status']]}** | {c['text']} | "
                 f"{c.get('clarified_as') or c.get('reason') or '—'} | {passed}/{ran} |")
    L += ["", "## Evidence by criterion", ""]
    for c in ev["coverage"]:
        L.append(f"### {c['id']} · {ICON[c['status']]}")
        if c["status"] in ("not-verifiable", "out-of-scope"):
            L += [f"Reason: {c['reason']}", ""]
            continue
        if c.get("missing_suites"):
            L.append(f"- Missing tests in suite(s): {', '.join(c['missing_suites'])}")
        for t in c["tests"]:
            proj = f"/{t['project']}" if t["project"] else ""
            L.append(f"- {t['status'].upper()} · [{t['suite']}{proj}] {t['name']}")
            if t["message"]:
                L.append(f"  - `{t['message']}`")
            for a in t["attachments"]:
                L.append(f"  - screenshot: `{a}`")
        L.append("")
    r = ev["regression"]
    L += ["## Existing regression tests (untagged)", "", f"{r['passed']}/{r['total']} passed."]
    L += [f"- FAIL {f}" for f in r["failed"]]
    if ev["unplanned_ac_tags"]:
        L += ["", f"Tests tagged with ACs not in the plan: {', '.join(ev['unplanned_ac_tags'])}"]
    L += ["", "## Suites", ""]
    for n, s in ev["suites"].items():
        L.append(f"- **{n}**: exit {s['exit_code']}, {s['cases']} test case(s), log `{s['log']}`")
    if problems:
        L += ["", "## Plan problems", ""] + [f"- {p}" for p in problems]
    L += ["", "---", "", "Gate 3 is a human decision. Record it with:", "",
          f"`python3 .claude/skills/verify-feature/scripts/verify.py approve {key} --by \"<your name>\" "
          "--decision approved|rejected --note \"...\"`", ""]
    write_text(d / "VERIFICATION_REPORT.md", "\n".join(L))
    return rep


def comment_text(rep: dict) -> str:
    lines = [f"AI-assisted verification · {rep['verdict']}",
             f"Run {rep['run_id']} ({rep['mode']}, {rep['environment']})"]
    lines += [f"- {r}" for r in rep["reasons"]]
    lines.append("Coverage:")
    for c in rep["coverage"]:
        lines.append(f"  {c['id']}: {ICON[c['status']]} ({c['passed']}/{c['tests']})")
    lines.append(f"Gates: G1 {rep['gates']['gate1_clarify']} · G2 {rep['gates']['gate2_promote']} · G3 pending human")
    lines.append(f"Full report: verification/{rep['story']}/VERIFICATION_REPORT.md")
    return "\n".join(lines)


def post(cfg: dict, key: str) -> dict:
    rep = read_json(out_dir(cfg, key) / "report.json")
    return jira.adapter(cfg).add_comment(key, "verify-feature (Claude)", comment_text(rep))


def approve(cfg: dict, key: str, by: str, decision: str, note: str, transition: str | None) -> dict:
    if decision not in ("approved", "rejected"):
        raise VerifyError("--decision must be 'approved' or 'rejected'.")
    rep = read_json(out_dir(cfg, key) / "report.json")
    if decision == "approved" and rep["verdict"] != "VERIFIED" and not note:
        raise VerifyError(f"Verdict is {rep['verdict']}. Approving anyway needs a --note explaining why.")
    record = {"story": key, "decision": decision, "by": by, "at": now_iso(), "note": note,
              "verdict_at_decision": rep["verdict"], "run_id": rep["run_id"]}
    write_json(out_dir(cfg, key) / "gate3-approval.json", record)
    j = jira.adapter(cfg)
    j.add_comment(key, by, f"Gate 3 · {decision.upper()} (verdict was {rep['verdict']}). {note}".strip())
    if transition:
        j.transition(key, transition)
    return record
