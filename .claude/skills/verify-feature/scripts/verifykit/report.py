"""Verification report, Jira comment, and the human approval record (Gate 3)."""
from __future__ import annotations

import re
import shlex
from pathlib import Path

from . import jira
from .guardrails import unapproved_tests
from .inspect_repo import scan_tests
from .plan import validate as validate_plan
from .util import VerifyError, now_iso, out_dir, read_json, verify_cmd, write_json, write_text

ICON = {"pass": "PASS", "fail": "FAIL", "missing": "NOT COVERED", "not-verifiable": "NOT VERIFIABLE",
        "out-of-scope": "OUT OF SCOPE", "unresolved": "UNRESOLVED", "blocked": "BLOCKED"}
ORIGIN = {"committed": "", "unpromoted": " · unpromoted", "unknown": " · origin unknown"}


def verdict(ev: dict, gate1_passed: bool, plan_problems: list[str], proposed: list[str]) -> tuple[str, list[str]]:
    """The verdict is computed from evidence only. The rules for NOT VERIFIED are unchanged:
    executed tests failed, or a suite ran and produced no results. Everything that could not be
    shown (open questions, blocked or withheld work, unreviewed or non-pipeline evidence) is
    INCOMPLETE. Nothing that did not run is ever counted as passing.
    """
    reasons: list[str] = []
    cov = ev["coverage"]
    failing = [c["id"] for c in cov if c["status"] == "fail"]
    suite_errors = [n for n, s in ev["suites"].items() if s.get("error")]
    if failing:
        reasons.append(f"Failing criteria: {', '.join(failing)}")
    if ev["regression"]["failed"]:
        reasons.append(f"{len(ev['regression']['failed'])} existing regression test(s) failing")
    if suite_errors:
        reasons.append(f"Suite(s) errored without results: {', '.join(suite_errors)}")
    if reasons:
        return "NOT VERIFIED", reasons

    by = lambda st: [c["id"] for c in cov if c["status"] == st]  # noqa: E731
    g1 = ev.get("gate1") or {}
    if not gate1_passed:
        if g1.get("open"):
            unresolved = ", ".join(f"{ac} ({', '.join(q)})" for ac, q in g1.get("open_by_ac", {}).items())
            story_level = g1.get("story_level_open", [])
            reasons.append(f"Gate 1 has {len(g1['open'])} open question(s)"
                           + (f"; unresolved criteria: {unresolved}" if unresolved else "")
                           + (f"; story-level: {', '.join(story_level)}" if story_level else ""))
        else:
            reasons.append("Gate 1 has unanswered clarification questions")
    if plan_problems:
        reasons.append(f"Plan has {len(plan_problems)} problem(s)")
    for name, s in ev["suites"].items():
        if s.get("status", "ran") == "blocked":
            reasons.append(f"Suite '{name}' blocked, not run: {s.get('reason', '')}")
        elif s.get("status", "ran") == "not-started":
            reasons.append(f"Suite '{name}' could not start: {s.get('reason', '')}")
    if by("blocked"):
        reasons.append(f"No evidence because planned tests were blocked or withheld: {', '.join(by('blocked'))}")
    if by("missing"):
        reasons.append(f"No passing evidence for: {', '.join(by('missing'))}")
    if by("not-verifiable"):
        reasons.append(f"Not verifiable as written: {', '.join(by('not-verifiable'))}")
    if proposed:
        withheld = ev.get("mode") == "pipeline" and ev.get("unpromoted", {}).get("files")
        reasons.append(f"{len(proposed)} test file(s) still @ai-proposed (Gate 2 open)"
                       + ("; withheld from this pipeline run" if withheld else ""))
    wt = ev.get("working_tree") or {}
    if ev["mode"] == "pipeline" and (wt.get("protected_source_changed") or wt.get("committed_tests_changed")):
        changed = wt.get("protected_source_changed", []) + wt.get("committed_tests_changed", [])
        reasons.append(f"Pipeline evidence is not from the committed revision; uncommitted changes to "
                       f"application code or reviewed tests: {', '.join(changed[:5])}")
    if ev["mode"] != "pipeline":
        reasons.append("Evidence is from interactive mode; re-run in pipeline mode before approval")
    if reasons:
        return "INCOMPLETE", reasons
    return "VERIFIED", ["Every in-scope criterion has passing, traced evidence"]


# ---- developer-facing findings -------------------------------------------------------------

# Values must be on the same line as the label ([ \t], not \s, so a heading ending in ':' never
# captures the next line). Playwright prints "Expected: x / Received: y"; node:assert prints
# "actual !== expected" and an object dump with "actual: x," / "expected: y,".
_EXPECTED = re.compile(r"^[ \t]*Expected(?:[ \t][\w ]{0,20})?:[ \t]*(\S.*?)[ \t]*$", re.M | re.I)
_RECEIVED = re.compile(r"^[ \t]*(?:Received|Actual)(?:[ \t][\w ]{0,20})?:[ \t]*(\S.*?)[ \t]*$", re.M | re.I)
_STRICT = re.compile(r"^[ \t]*(\S.*?) !== (\S.*?)[ \t]*$", re.M)  # node:assert strictEqual(actual, expected)


def _clean(v: str | None) -> str | None:
    return v.rstrip(",;").strip() if v else v


def expected_observed(text: str) -> tuple[str | None, str | None]:
    """Read expected and observed values only where the framework printed them. Never guessed."""
    if not text:
        return None, None
    m = _STRICT.search(text)
    if m:
        return _clean(m.group(2)), _clean(m.group(1))
    e, r = _EXPECTED.search(text), _RECEIVED.search(text)
    return _clean(e.group(1) if e else None), _clean(r.group(1) if r else None)


def _focus_command(suite: dict, test_paths: list[str], name: str, project: str) -> str | None:
    """A command that re-runs just this test, for frameworks whose filter is known (checked against
    Playwright and node:test on the demo app). Otherwise None: the suite command is given instead."""
    fw, cwd = suite.get("framework", ""), suite.get("cwd", ".").rstrip("/")
    if fw == "playwright":
        return f"npx playwright test -g {shlex.quote(re.escape(name))}" + (f" --project={project}" if project else "")
    if fw == "node-test":
        # Called directly: options passed through `npm run` after the file glob are ignored by node.
        rel_paths = [p[len(cwd) + 1:] if cwd not in ("", ".") and p.startswith(cwd + "/") else p for p in test_paths]
        files = " ".join(shlex.quote(f"{p.rstrip('/')}/**/*.test.*") for p in rel_paths) or "."
        return f"node --test --test-name-pattern={shlex.quote(re.escape(name))} {files}"
    if fw == "pytest":
        return f"python3 -m pytest -k {shlex.quote(name)}"
    return None


def _traces(attachments: list[str], artifacts: list[str]) -> list[str]:
    dirs = {a.rsplit("/", 1)[0] for a in attachments if "/" in a}
    return [a for a in artifacts if a.endswith(".zip") and a.rsplit("/", 1)[0] in dirs]


def build_findings(cfg: dict, ev: dict, key: str, manifest: dict) -> list[dict]:
    suites_cfg = cfg.get("suites", {})
    open_by_ac = (ev.get("gate1") or {}).get("open_by_ac", {})
    wt = ev.get("working_tree") or {}
    revision = (ev.get("git_sha") or "unknown") + (" + uncommitted changes" if wt.get("clean") is False else "")
    artifacts = {s["name"]: s.get("artifacts", []) for s in manifest.get("suites", [])}
    out: list[dict] = []

    def common(suite_name: str) -> dict:
        st = ev["suites"][suite_name]
        env = " ".join(f"{k}={shlex.quote(v)}" for k, v in st.get("env", {}).items() if v)
        return {
            "story": key, "suite": suite_name, "environment": ev["environment"], "target": ev.get("target", {}),
            "revision": revision, "run_id": ev["run_id"], "timestamp": ev.get("finished") or ev.get("started"),
            "log": st.get("log", ""),
            "reproduce": {"suite_command": f"cd {st.get('cwd') or '.'} && {(env + ' ') if env else ''}{st.get('command', '')}"},
        }

    for c in ev["cases"]:
        if c["status"] != "fail":
            continue
        acs = c.get("ac", [])
        if acs and any(a in open_by_ac for a in acs):
            cls = "requirement ambiguity"
        elif c.get("origin") == "committed":
            cls = "confirmed failure"
        else:
            cls = "suspected defect (unreviewed test)"
        exp, obs = expected_observed(c.get("details") or c.get("message", ""))
        f = common(c["suite"]) | {
            "kind": "acceptance" if acs else "regression", "classification": cls,
            "acceptance_criteria": acs, "open_questions": sorted({q for a in acs for q in open_by_ac.get(a, [])}),
            "test": c["name"], "project": c.get("project", ""), "origin": c.get("origin", "unknown"),
            "expected": exp, "observed": obs, "message": c.get("message", ""), "details": c.get("details", ""),
            "screenshots": [a for a in c.get("attachments", []) if a.lower().endswith((".png", ".jpg", ".jpeg"))],
            "traces": _traces(c.get("attachments", []), artifacts.get(c["suite"], [])),
        }
        focus = _focus_command(suites_cfg.get(c["suite"], {}), suites_cfg.get(c["suite"], {}).get("test_paths", []),
                               c["name"], c.get("project", ""))
        if focus:
            f["reproduce"]["focus_command"] = f"cd {ev['suites'][c['suite']].get('cwd') or '.'} && {focus}"
        out.append(f)

    for name, st in ev["suites"].items():
        if st.get("error"):
            exit_code = st.get("exit_code")
            out.append(common(name) | {
                "kind": "execution", "classification": "could not produce results",
                "acceptance_criteria": [], "test": None,
                "message": ("suite timed out" if exit_code is None else f"suite exited {exit_code} without any test results"),
                "expected": None, "observed": None,
            })
    for i, f in enumerate(out, 1):
        f["id"] = f"F-{i}"
    return [{"id": f.pop("id"), **f} for f in out]


def unpromoted_in_suites(cfg: dict) -> list[str]:
    """Gate 2 covers the test files under the configured suites' test_paths (see gates.md).
    Marker text elsewhere (docs, fixtures, the engine's own tests) is not a pending promotion.
    With no test_paths configured, every test file in the repository counts."""
    paths = [p for s in cfg.get("suites", {}).values() for p in s.get("test_paths", [])]
    if paths:
        return unapproved_tests(Path(cfg["_root"]), paths)
    return [t["path"] for t in scan_tests(Path(cfg["_root"])) if t["ai_proposed"]]


def build(cfg: dict, key: str) -> dict:
    from .gaps import status as gate1_status
    from .runner import latest_run
    d = out_dir(cfg, key)
    ev = read_json(d / "evidence.json")
    story = read_json(d / "story.json")
    g1 = gate1_status(cfg, key)
    ev["gate1"] = g1  # answers given since the run count; open ones keep their criteria unresolved
    open_by_ac = (g1 or {}).get("open_by_ac", {})
    for c in ev["coverage"]:
        if c["disposition"] == "verify" and c["status"] in ("pass", "missing", "blocked") and open_by_ac.get(c["id"]):
            c["status"], c["open_questions"] = "unresolved", open_by_ac[c["id"]]
        elif c["status"] == "unresolved" and not open_by_ac.get(c["id"]):
            ran_pass = any(x["status"] == "pass" for x in c.get("tests", []))
            c["status"] = "pass" if ran_pass and not c.get("missing_suites") else (
                "blocked" if c.get("blocked_suites") or c.get("withheld_suites") else "missing")
            c["open_questions"] = []
    gate1 = g1 or {"passed": False, "open": ["not run"]}
    problems = validate_plan(cfg, key)
    proposed = unpromoted_in_suites(cfg)
    v, reasons = verdict(ev, gate1.get("passed", False), problems, proposed)
    try:
        manifest = read_json(latest_run(cfg, key, ev["run_id"]) / "run.json")
    except VerifyError:
        manifest = {}
    findings = build_findings(cfg, ev, key, manifest)
    write_json(d / "findings.json", {"story": key, "run_id": ev["run_id"], "verdict": v, "findings": findings})

    statuses = [c["status"] for c in ev["cases"]]
    not_run = {n: {"status": s["status"], "reason": s.get("reason", "")}
               for n, s in ev["suites"].items() if s.get("status", "ran") != "ran"}
    open_detail = (g1 or {}).get("open_detail", [])
    rep = {
        "story": key, "summary": story.get("summary", ""), "verdict": v, "reasons": reasons,
        "generated": now_iso(), "run_id": ev["run_id"], "mode": ev["mode"], "environment": ev["environment"],
        "git_sha": ev.get("git_sha"), "working_tree_clean": (ev.get("working_tree") or {}).get("clean"),
        "gates": {
            "gate1_clarify": "passed" if gate1.get("passed") else "open",
            "gate2_promote": "passed" if not proposed else f"open ({len(proposed)} file(s))",
            "gate3_approve": "pending human decision",
        },
        "tests": {"passed": statuses.count("pass"), "failed": statuses.count("fail"),
                  "skipped": statuses.count("skip"), "suites_not_run": sorted(not_run)},
        "not_run": not_run,
        "withheld": (ev.get("unpromoted") or {}).get("files", []) if ev["mode"] == "pipeline" else [],
        "open_questions": open_detail,
        "findings": {"total": len(findings), "by_classification": _count(f["classification"] for f in findings)},
        "coverage": [
            {k: c.get(k, "") for k in ("id", "status", "text", "clarified_as", "reason")}
            | {"tests": sum(1 for t in c["tests"] if t["status"] != "skip"),
               "passed": sum(1 for t in c["tests"] if t["status"] == "pass"),
               "open_questions": c.get("open_questions", []), "evidence_basis": c.get("evidence_basis", "")}
            for c in ev["coverage"]
        ],
        "regression": dict(ev["regression"]),
    }
    write_json(d / "report.json", rep)
    write_text(d / "VERIFICATION_REPORT.md", _markdown(key, story, ev, rep, findings, problems, open_detail, cfg["_root"]))
    return rep


def _count(items) -> dict:
    out: dict = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return out


def _markdown(key, story, ev, rep, findings, problems, open_detail, root=".") -> str:
    wt = ev.get("working_tree") or {}
    t = rep["tests"]
    L = [f"# Verification Report · {key}", "", f"**{story.get('summary', '')}**", "",
         f"## Verdict: {rep['verdict']}", ""] + [f"- {r}" for r in rep["reasons"]] + [
        "", f"Run `{ev['run_id']}` · mode **{ev['mode']}** · environment **{ev['environment']}**"
            + (f" · commit `{ev['git_sha']}`" if ev.get("git_sha") else "")
            + (" (with uncommitted changes)" if wt.get("clean") is False else ""),
        "", f"Tests: **{t['passed']} passed · {t['failed']} failed · {t['skipped']} skipped**"
            + (f" · suites not run: {', '.join(t['suites_not_run'])}" if t["suites_not_run"] else ""),
        "", "## Gates", "",
        "- Gate 1 · Clarify (exception-based): **"
        + ("all questions answered" if rep["gates"]["gate1_clarify"] == "passed"
           else f"{len(open_detail)} open question(s)" if open_detail else "not run") + "**",
        f"- Gate 2 · Promote tests: **{rep['gates']['gate2_promote']}**",
        f"- Gate 3 · Human approval: **{rep['gates']['gate3_approve']}**",
        "", "## Coverage vs acceptance criteria", "",
        "| AC | Result | Evidence | Criterion | Clarified as | Passed / ran |", "|---|---|---|---|---|---|"]
    for c in ev["coverage"]:
        passed = sum(1 for x in c["tests"] if x["status"] == "pass")
        ran = sum(1 for x in c["tests"] if x["status"] != "skip")
        basis = c.get("evidence_basis") or "—"
        note = c.get("clarified_as") or c.get("reason") or (
            f"Open: {', '.join(c['open_questions'])}" if c.get("open_questions") else "—")
        L.append(f"| {c['id']} | **{ICON[c['status']]}** | {basis} | {c['text']} | {note} | {passed}/{ran} |")
    L += ["", "Evidence: *reviewed* = only promoted tests; *unreviewed* = AI-proposed or origin unknown; "
          "*mixed* = both. Unreviewed evidence never satisfies the pipeline requirement for VERIFIED.", ""]

    if open_detail:
        L += ["## Open questions (testing continued)", "", "| Question | Criteria | Topic | Owner |", "|---|---|---|---|"]
        L += [f"| {q['id']} | {', '.join(q['acs']) or 'story'} | {q['topic']} | {q['owner']} |" for q in open_detail]
        L += ["", "Unanswered questions are never treated as approval. Affected criteria stay UNRESOLVED.", ""]

    if rep["not_run"] or rep["withheld"]:
        L += ["## Not run", ""]
        for n, s in rep["not_run"].items():
            L.append(f"- Suite **{n}** · {s['status'].upper()} · {s['reason']}")
        for f in rep["withheld"]:
            L.append(f"- `{f}` · WITHHELD from pipeline run · unpromoted (Gate 2)")
        L.append("")

    if findings:
        L += ["## Findings for developers", "",
              "Full detail, including failure output and reproduction commands, is in `findings.json`.", ""]
        for f in findings:
            ac = ", ".join(f.get("acceptance_criteria") or []) or f["kind"]
            L.append(f"### {f['id']} · {f['classification']} · {ac}")
            if f.get("test"):
                L.append(f"- Test: [{f['suite']}{'/' + f['project'] if f.get('project') else ''}] {f['test']}")
            L.append(f"- Expected: {f['expected'] or 'not stated in the failure output'}")
            L.append(f"- Observed: {f['observed'] or 'not stated in the failure output'}")
            if f.get("message"):
                L.append(f"- Message: `{f['message']}`")
            for s_ in f.get("screenshots", []):
                L.append(f"- Screenshot: `{s_}`")
            for tr in f.get("traces", []):
                L.append(f"- Trace: `{tr}`")
            L.append(f"- Reproduce: `{f['reproduce'].get('focus_command') or f['reproduce']['suite_command']}`")
            L.append(f"- Revision `{f['revision']}` · {f['environment']} · {f['timestamp']}")
            L.append("")

    L += ["## Evidence by criterion", ""]
    for c in ev["coverage"]:
        L.append(f"### {c['id']} · {ICON[c['status']]}")
        if c["status"] in ("not-verifiable", "out-of-scope"):
            L += [f"Reason: {c['reason']}", ""]
            continue
        if c.get("open_questions"):
            L.append(f"- Waiting on: {', '.join(c['open_questions'])}. Not reported as passing until answered.")
        if c.get("blocked_suites"):
            L.append(f"- Planned suite(s) did not run: {', '.join(c['blocked_suites'])}")
        if c.get("withheld_suites"):
            L.append(f"- Tests withheld from this pipeline run, not yet promoted (Gate 2): {', '.join(c['withheld_suites'])}")
        accounted = c.get("blocked_suites", []) + c.get("withheld_suites", [])
        other_missing = [s for s in c.get("missing_suites", []) if s not in accounted]
        if other_missing:
            L.append(f"- Missing tests in suite(s): {', '.join(other_missing)}")
        for x in c["tests"]:
            proj = f"/{x['project']}" if x["project"] else ""
            L.append(f"- {x['status'].upper()} · [{x['suite']}{proj}{ORIGIN.get(x.get('origin', 'committed'), '')}] {x['name']}")
            if x["message"]:
                L.append(f"  - `{x['message']}`")
            for a in x["attachments"]:
                L.append(f"  - screenshot: `{a}`")
        L.append("")
    r = ev["regression"]
    L += ["## Existing regression tests (untagged)", "", f"{r['passed']}/{r['total']} passed."]
    L += [f"- FAIL {f}" for f in r["failed"]]
    if ev["unplanned_ac_tags"]:
        L += ["", f"Tests tagged with ACs not in the plan: {', '.join(ev['unplanned_ac_tags'])}"]
    L += ["", "## Suites", ""]
    for n, s in ev["suites"].items():
        state = s.get("status", "ran")
        if state == "ran":
            L.append(f"- **{n}**: exit {s['exit_code']}, {s['cases']} test case(s), log `{s['log']}`")
        else:
            L.append(f"- **{n}**: {state.upper()}, {s.get('reason', '')}")
    if wt.get("clean") is False:
        L += ["", "## Working tree", "", f"Uncommitted changes at run time: {len(wt.get('changed', []))} path(s)."]
        if wt.get("protected_source_changed"):
            L.append(f"- Application code changed: {', '.join(wt['protected_source_changed'])}")
        if wt.get("committed_tests_changed"):
            L.append(f"- Reviewed tests changed: {', '.join(wt['committed_tests_changed'])}")
    if problems:
        L += ["", "## Plan problems", ""] + [f"- {p}" for p in problems]
    L += ["", "---", "", "Gate 3 is a human decision. Record it with:", "",
          f"`{verify_cmd(root)} approve {key} --by \"<your name>\" "
          "--decision approved|rejected --note \"...\"`", ""]
    return "\n".join(L)


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
