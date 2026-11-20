#!/usr/bin/env python3
"""verify.py — deterministic engine behind the verify-feature skill.

Claude decides WHAT to verify (plan, tests, judgement). This CLI decides
nothing: it pulls the story, runs the repo's own frameworks, and computes
evidence the same way every time. Standard library only.

  story     <KEY>                 pull story, assign AC IDs
  inspect   <KEY>                 inventory frameworks, tests, AC tags
  gaps      <KEY> [--force]       Gate 1: deterministic clarification questions
  gate1     <KEY> --check         Gate 1: pass only when every question is answered
  plan      <KEY> --init|--check|--render
  run       <KEY> [--suite a,b] [--mode interactive|pipeline] [--env local]
  evidence  <KEY> [--run ID]      parse JUnit, map tests to ACs
  report    <KEY>                 verdict + VERIFICATION_REPORT.md
  post      <KEY>                 post the summary to Jira as a comment
  all       <KEY> [run options]   run + evidence + report
  proposed                        list tests still marked @ai-proposed
  promote   <file> --by NAME [--story KEY]   Gate 2 (a person runs this)
  approve   <KEY> --by NAME --decision approved|rejected [--note] [--transition Done]   Gate 3 (a person)
  init      [--force]             write a starter verify.config.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verifykit import config_init, evidence, gaps, inspect_repo, plan, promote, report, runner, story  # noqa: E402
from verifykit.util import VerifyError, load_config, repo_root  # noqa: E402


# Exit codes for CI: 0 VERIFIED, 3 INCOMPLETE, 4 NOT VERIFIED (1 = usage/guardrail error, 2 = gate/plan check failed)
VERDICT_EXIT = {"VERIFIED": 0, "INCOMPLETE": 3, "NOT VERIFIED": 4}


def _print(obj) -> None:
    print(json.dumps(obj, indent=2) if not isinstance(obj, str) else obj)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="verify.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def keyed(name, **kw):
        p = sub.add_parser(name, **kw)
        p.add_argument("key")
        return p

    keyed("story")
    keyed("inspect")
    keyed("gaps").add_argument("--force", action="store_true")
    keyed("gate1").add_argument("--check", action="store_true", required=True)
    pp = keyed("plan")
    g = pp.add_mutually_exclusive_group(required=True)
    g.add_argument("--init", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--render", action="store_true")
    pp.add_argument("--force", action="store_true")
    for name in ("run", "all"):
        rp = keyed(name)
        rp.add_argument("--suite", default="", help="comma-separated suite names (default: all)")
        rp.add_argument("--mode", choices=["interactive", "pipeline"], default="interactive")
        rp.add_argument("--env", default="local")
    keyed("evidence").add_argument("--run", default=None)
    keyed("report")
    keyed("post")
    sub.add_parser("proposed")
    pr = sub.add_parser("promote")
    pr.add_argument("file")
    pr.add_argument("--by", required=True)
    pr.add_argument("--story", default=None)
    ap_ = keyed("approve")
    ap_.add_argument("--by", required=True)
    ap_.add_argument("--decision", required=True, choices=["approved", "rejected"])
    ap_.add_argument("--note", default="")
    ap_.add_argument("--transition", default=None)
    sub.add_parser("init").add_argument("--force", action="store_true")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "init":
            _print(f"Wrote {config_init.init(Path.cwd(), a.force)}. Review every suite before running.")
            return 0
        cfg = load_config(repo_root())
        if a.cmd == "story":
            s = story.pull(cfg, a.key)
            _print({"key": s["key"], "summary": s["summary"], "acceptance_criteria": s["acceptance_criteria"]})
        elif a.cmd == "inspect":
            inv = inspect_repo.inspect(cfg, a.key)
            _print({"frameworks": [f"{f['framework']} ({f['where']})" for f in inv["frameworks"]],
                    "configured_suites": inv["configured_suites"], "summary": inv["summary"]})
        elif a.cmd == "gaps":
            md, findings = gaps.run(cfg, a.key, a.force)
            _print(f"{len(findings)} question(s) written to {md}")
            for f in findings:
                print(f"  {f['id']} {f['ac']:<6} {f['rule']}")
        elif a.cmd == "gate1":
            r = gaps.check(cfg, a.key)
            _print(r)
            return 0 if r["passed"] else 2
        elif a.cmd == "plan":
            if a.init:
                _print(f"Wrote {plan.init(cfg, a.key, a.force)}. Fill in checks for each AC.")
            elif a.check:
                problems = plan.validate(cfg, a.key)
                _print({"ok": not problems, "problems": problems})
                return 0 if not problems else 2
            else:
                _print(f"Wrote {plan.render(cfg, a.key)}")
        elif a.cmd in ("run", "all"):
            suites = [s for s in a.suite.split(",") if s]
            m = runner.run(cfg, a.key, suites, a.mode, a.env)
            failed = [s["name"] for s in m["suites"] if s["exit_code"] != 0]
            print(f"\nRun {m['run_id']} finished. Suites with non-zero exit: {failed or 'none'}")
            if a.cmd == "all":
                evidence.collect(cfg, a.key)
                rep = report.build(cfg, a.key)
                print(f"Verdict: {rep['verdict']}")
                for r in rep["reasons"]:
                    print(f"  - {r}")
                return VERDICT_EXIT[rep["verdict"]]
        elif a.cmd == "evidence":
            ev = evidence.collect(cfg, a.key, a.run)
            _print({"run_id": ev["run_id"], "coverage": {c["id"]: c["status"] for c in ev["coverage"]},
                    "regression": {k: v for k, v in ev["regression"].items() if k != "failed"}
                    | {"failed": len(ev["regression"]["failed"])}})
        elif a.cmd == "report":
            rep = report.build(cfg, a.key)
            _print({"verdict": rep["verdict"], "reasons": rep["reasons"],
                    "report": f"{cfg.get('output_dir', 'verification')}/{a.key}/VERIFICATION_REPORT.md"})
            return VERDICT_EXIT[rep["verdict"]]
        elif a.cmd == "post":
            _print({"posted": report.post(cfg, a.key)})
        elif a.cmd == "proposed":
            _print({"ai_proposed": promote.proposed(cfg)})
        elif a.cmd == "promote":
            _print(promote.promote(cfg, a.file, a.by, a.story))
        elif a.cmd == "approve":
            _print(report.approve(cfg, a.key, a.by, a.decision, a.note, a.transition))
        return 0
    except VerifyError as e:
        print(f"verify: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
