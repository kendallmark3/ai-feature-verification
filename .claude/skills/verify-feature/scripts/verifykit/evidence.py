"""Turn a run's JUnit XML into evidence and AC coverage.

JUnit XML is the common format: Playwright, node:test, pytest, Jest (jest-junit),
Vitest, Maven Surefire, Gradle, go (gotestsum), .NET and Cypress can all emit it.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .plan import load as load_plan
from .runner import latest_run
from .util import VerifyError, out_dir, read_json, write_json

STORY_KEY = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
AC_ID = re.compile(r"\b(AC-\d+)\b")
ATTACHMENT = re.compile(r"\[\[ATTACHMENT\|(.+?)\]\]")


def _status(case: ET.Element) -> tuple[str, str]:
    for tag, status in (("failure", "fail"), ("error", "fail")):
        el = case.find(tag)
        if el is not None:
            # Prefer the body: some reporters flatten newlines out of the message attribute.
            body = [l.strip() for l in (el.text or "").splitlines() if l.strip()]
            body = [re.sub(r"^\[?Error(?: \[\w+\])?:\s*", "", l) for l in body[:2]]
            msg = " — ".join(body) if body else (el.get("message") or "failed")
            return status, msg[:400]
    if case.get("failure"):
        return "fail", case.get("failure", "")[:400]
    if case.find("skipped") is not None:
        return "skip", ""
    return "pass", ""


def parse_junit(path: Path, suite: str) -> list[dict]:
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise VerifyError(f"Could not parse JUnit XML {path}: {e}") from e
    cases = []
    root = tree.getroot()
    parents = {c: p for p in root.iter() for c in p}
    for case in root.iter("testcase"):
        parent = parents.get(case)
        project = parent.get("hostname", "") if parent is not None and parent.tag == "testsuite" else ""
        status, message = _status(case)
        out = " ".join((el.text or "") for el in case.iter("system-out"))
        name = case.get("name", "")
        cases.append({
            "suite": suite,
            "project": project if project not in ("", "localhost") else "",
            "name": name,
            "classname": case.get("classname", ""),
            "time_s": float(case.get("time") or 0),
            "status": status,
            "message": message,
            "attachments": ATTACHMENT.findall(out),
        })
    return cases


def _tags(case: dict, key: str) -> list[str]:
    text = f"{case['name']} {case['classname']}"
    keys = set(STORY_KEY.findall(text)) - set(AC_ID.findall(text))
    if keys and key not in keys:
        return []  # tagged for another story
    return sorted(set(AC_ID.findall(text)))


def collect(cfg: dict, key: str, run_id: str | None = None) -> dict:
    root = Path(cfg["_root"])
    run_dir = latest_run(cfg, key, run_id)
    manifest = read_json(run_dir / "run.json")
    plan = load_plan(cfg, key)

    cases, suite_status = [], {}
    for s in manifest["suites"]:
        found = []
        for j in s["junit"]:
            found += parse_junit(root / j, s["name"])
        for c in found:
            c["attachments"] = [
                next((a for a in s["artifacts"] if a.endswith(att.replace("\\", "/"))), att) for att in c["attachments"]
            ]
        cases += found
        suite_status[s["name"]] = {
            "exit_code": s["exit_code"], "cases": len(found), "log": s["log"],
            "error": s["exit_code"] != 0 and not found,
        }

    for c in cases:
        c["ac"] = _tags(c, key)

    plan_ids = {a["id"] for a in plan["acs"]}
    coverage = []
    for ac in plan["acs"]:
        tagged = [c for c in cases if ac["id"] in c["ac"]]
        entry = {"id": ac["id"], "text": ac["text"], "clarified_as": ac.get("clarified_as", ""),
                 "disposition": ac["disposition"], "reason": ac.get("reason", ""),
                 "tests": [{k: c[k] for k in ("suite", "project", "name", "status", "message", "attachments")} for c in tagged]}
        if ac["disposition"] != "verify":
            entry["status"] = ac["disposition"]
        else:
            planned_suites = sorted({ch["suite"] for ch in ac.get("checks", [])})
            # A suite counts only if a tagged test actually executed there (skipped tests don't).
            missing = [s for s in planned_suites
                       if not any(t["suite"] == s and t["status"] in ("pass", "fail") for t in tagged)]
            entry["missing_suites"] = missing
            if any(t["status"] == "fail" for t in tagged):
                entry["status"] = "fail"
            elif missing or not tagged:
                entry["status"] = "missing"
            else:
                entry["status"] = "pass"
        coverage.append(entry)

    unplanned = sorted({a for c in cases for a in c["ac"] if a not in plan_ids})
    untagged = [c for c in cases if not c["ac"]]
    evidence = {
        "story": key, "run_id": manifest["run_id"], "mode": manifest["mode"], "environment": manifest["environment"],
        "git_sha": manifest.get("git_sha"), "suites": suite_status, "coverage": coverage,
        "unplanned_ac_tags": unplanned,
        "regression": {
            "total": len(untagged),
            "passed": sum(1 for c in untagged if c["status"] == "pass"),
            "failed": [f"[{c['suite']}{'/' + c['project'] if c['project'] else ''}] {c['name']}: {c['message']}"
                       for c in untagged if c["status"] == "fail"],
        },
        "cases": cases,
    }
    write_json(out_dir(cfg, key) / "evidence.json", evidence)
    return evidence
