"""Regression tests for INTENT-001 (autonomous, evidence-based verification).

    python3 -m unittest discover -s tests/verifykit -v

Each end-to-end test builds a throwaway repository with a fake test framework
(`emit.py`, standard library only) that reads test files and writes JUnit XML,
so the real engine runs, blocks, withholds and reports exactly as it would on a
real project.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/verify-feature/scripts"))

import verify  # noqa: E402
from verifykit import gaps, report, runner  # noqa: E402
from verifykit.util import load_config, redact  # noqa: E402

# A fake framework. Each test file holds lines "TEST <title> | pass|fail|skip | <failure text>".
# Writes JUnit XML with the file name as classname (like Playwright), or "test" (like node:test)
# when --no-file is given. Records which files it saw, so tests can prove what was withheld.
EMIT = textwrap.dedent('''
    import pathlib, sys, xml.sax.saxutils as x
    suite, out = sys.argv[1], sys.argv[2]
    with_file = "--no-file" not in sys.argv
    files = sorted(pathlib.Path("tests", suite).glob("*.test.js"))
    pathlib.Path("seen-" + suite + ".txt").write_text("\\n".join(f.name for f in files))
    cases, failed = [], 0
    for f in files:
        for line in f.read_text().splitlines():
            if not line.startswith("TEST "):
                continue
            title, status, *rest = [p.strip() for p in line[5:].split("|")]
            cn = f.name if with_file else "test"
            body = ""
            if status == "fail":
                failed += 1
                body = "<failure message='failed'>" + x.escape((rest or [""])[0].replace("\\\\n", "\\n")) + "</failure>"
            elif status == "skip":
                body = "<skipped/>"
            cases.append(f"<testcase name={x.quoteattr(title)} classname={x.quoteattr(cn)}>{body}</testcase>")
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out).write_text("<testsuites><testsuite name='s'>" + "".join(cases) + "</testsuite></testsuites>")
    sys.exit(1 if failed else 0)
''')

GATE1_TEMPLATE = """# Gate 1 · Clarifications for DEMO-1

## Q-1 · AC-2 · UNMEASURED_NFR

Owner: Pat (Product)

Question: How fast?

Answer: {a1}

## Q-2 · STORY · NO_EXAMPLES

Question: Give an example?

Answer: {a2}
"""


class Repo:
    """A temporary repository wired to the real engine."""

    def __init__(self, suites=None, environments=None, protected=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "emit.py").write_text(EMIT)
        (self.root / "jira").mkdir()
        (self.root / "jira" / "DEMO-1.json").write_text(json.dumps({
            "key": "DEMO-1", "summary": "Demo story", "reporter": "Pat (Product)", "description": "d",
            "acceptance_criteria": ["Shows the total of 3 items", "Should be fast", "Bad codes show an error"],
        }))
        self.cfg = {
            "output_dir": "verification",
            "jira": {"adapter": "local", "path": "jira"},
            "environments": environments or {"local": {"BASE_URL": "", "allow_shared_data_writes": True},
                                             "uat": {"BASE_URL": "https://uat.example.com"}},
            "guardrails": {"allowed_commands": ["python3"], "deny_url_patterns": [],
                           "protected_paths": protected or ["app"], "max_runtime_seconds": 60},
            "suites": suites or {
                "api": self.suite("api"),
                "e2e": self.suite("e2e"),
            },
        }
        self.write_config()
        for s in self.cfg["suites"]:
            (self.root / "tests" / s).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def suite(name, **extra):
        return {"framework": "fake", "cwd": ".", "command": f"python3 emit.py {name} reports/{name}.xml",
                "junit": [f"reports/{name}.xml"], "artifacts": [], "test_paths": [f"tests/{name}"], **extra}

    def write_config(self):
        (self.root / "verify.config.json").write_text(json.dumps(self.cfg, indent=2))

    def test_file(self, suite, name, lines, proposed=False):
        header = "// @ai-proposed DEMO-1\n" if proposed else "// reviewed\n"
        p = self.root / "tests" / suite / name
        p.write_text(header + "\n".join(lines) + "\n")
        return p

    def plan(self, acs):
        d = self.root / "verification" / "DEMO-1"
        d.mkdir(parents=True, exist_ok=True)
        (d / "plan.json").write_text(json.dumps({"story": "DEMO-1", "acs": acs}))

    def gate1(self, a1="", a2="yes"):
        d = self.root / "verification" / "DEMO-1"
        d.mkdir(parents=True, exist_ok=True)
        (d / "gate1-clarifications.md").write_text(GATE1_TEMPLATE.format(a1=a1, a2=a2))

    def cli(self, *args):
        cwd = os.getcwd()
        buf = io.StringIO()
        try:
            os.chdir(self.root)
            with redirect_stdout(buf):
                code = verify.main(list(args))
        finally:
            os.chdir(cwd)
        return code, buf.getvalue()

    def config(self):
        return load_config(self.root)

    def json(self, name):
        return json.loads((self.root / "verification" / "DEMO-1" / name).read_text())

    def close(self):
        self.tmp.cleanup()


def ac(i, suites=("api",), disposition="verify", reason=""):
    return {"id": f"AC-{i}", "text": f"criterion {i}", "disposition": disposition, "reason": reason,
            "clarified_as": "",
            "checks": [{"id": f"C{i}{s}", "suite": s, "description": "d", "expected_evidence": ["junit"]}
                       for s in suites] if disposition == "verify" else []}


class RepoTest(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        self.r.cli("story", "DEMO-1")

    def tearDown(self):
        self.r.close()


# ---------------------------------------------------------------- SC-01, SC-05: clarification


class ExceptionBasedClarification(RepoTest):
    def test_gate1_maps_open_questions_to_their_criteria_and_owner(self):
        self.r.gate1(a1="", a2="")
        st = gaps.check(self.r.config(), "DEMO-1")
        self.assertFalse(st["passed"])
        self.assertEqual(st["open_by_ac"], {"AC-2": ["Q-1"]})
        self.assertEqual(st["story_level_open"], ["Q-2"])
        owners = {q["id"]: q["owner"] for q in st["open_detail"]}
        self.assertEqual(owners["Q-1"], "Pat (Product)")
        self.assertEqual(owners["Q-2"], "Pat (Product)")  # falls back to the story reporter

    def test_gaps_file_names_the_owner_and_does_not_say_testing_must_wait(self):
        self.r.cli("gaps", "DEMO-1")
        text = (self.r.root / "verification/DEMO-1/gate1-clarifications.md").read_text()
        self.assertIn("Owner: Pat (Product)", text)
        self.assertIn("Testing does not wait for these answers", text)

    def test_ambiguous_criterion_does_not_stop_unrelated_tests(self):
        self.r.gate1(a1="")  # AC-2 open
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 total | pass", "TEST DEMO-1 AC-2 speed | pass",
                                        "TEST DEMO-1 AC-3 error | pass"])
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        cov = {c["id"]: c["status"] for c in self.r.json("evidence.json")["coverage"]}
        self.assertEqual(cov, {"AC-1": "pass", "AC-2": "unresolved", "AC-3": "pass"})
        rep = self.r.json("report.json")
        self.assertEqual(rep["verdict"], "INCOMPLETE")
        self.assertEqual(code, 3)
        self.assertTrue(any("unresolved criteria: AC-2 (Q-1)" in x for x in rep["reasons"]))

    def test_unresolved_criterion_is_never_reported_as_passing(self):
        self.r.gate1(a1="")
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass",
                                        "TEST DEMO-1 AC-3 x | pass"])
        self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        ac2 = next(c for c in self.r.json("report.json")["coverage"] if c["id"] == "AC-2")
        self.assertEqual(ac2["status"], "unresolved")
        self.assertEqual(ac2["passed"], 1)  # the test passed, the criterion still is not shown as passing

    def test_answering_later_resolves_without_rerunning(self):
        self.r.gate1(a1="")
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass",
                                        "TEST DEMO-1 AC-3 x | pass"])
        self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.r.gate1(a1="Under 300 ms at p95")
        code, _ = self.r.cli("report", "DEMO-1")
        self.assertEqual((code, self.r.json("report.json")["verdict"]), (0, "VERIFIED"))

    def test_failure_on_ambiguous_criterion_is_still_not_verified_and_classed_as_ambiguity(self):
        self.r.gate1(a1="")
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | fail | took 9s",
                                        "TEST DEMO-1 AC-3 x | pass"])
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 4)
        f = self.r.json("findings.json")["findings"]
        self.assertEqual([x["classification"] for x in f], ["requirement ambiguity"])
        self.assertEqual(f[0]["open_questions"], ["Q-1"])

    def test_unresolved_criterion_may_have_no_checks_yet(self):
        self.r.gate1(a1="")
        no_checks = ac(2)
        no_checks["checks"] = []
        self.r.plan([ac(1), no_checks, ac(3)])
        code, out = self.r.cli("plan", "DEMO-1", "--check")
        self.assertEqual(code, 0, out)
        self.r.gate1(a1="answered")
        code, _ = self.r.cli("plan", "DEMO-1", "--check")
        self.assertEqual(code, 2)  # once answered, it needs checks like any other criterion

    def test_no_gate1_file_is_incomplete_not_approval(self):
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass",
                                        "TEST DEMO-1 AC-3 x | pass"])
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 3)


# ---------------------------------------------------------------- SC-06, SC-08: unpromoted tests


class UnpromotedTests(RepoTest):
    def setUp(self):
        super().setUp()
        self.r.gate1(a1="answered")
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "reviewed.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-3 x | pass"])
        self.proposed = self.r.test_file("api", "proposed.test.js", ["TEST DEMO-1 AC-2 new | pass"], proposed=True)

    def test_interactive_runs_unpromoted_tests_and_labels_them(self):
        self.r.cli("all", "DEMO-1", "--mode", "interactive")
        self.assertIn("proposed.test.js", (self.r.root / "seen-api.txt").read_text())
        ev = self.r.json("evidence.json")
        origins = {c["name"]: c["origin"] for c in ev["cases"]}
        self.assertEqual(origins["DEMO-1 AC-2 new"], "unpromoted")
        self.assertEqual(origins["DEMO-1 AC-1 x"], "committed")
        bases = {c["id"]: c["evidence_basis"] for c in ev["coverage"]}
        self.assertEqual(bases["AC-2"], "unreviewed")
        self.assertEqual(bases["AC-1"], "reviewed")
        self.assertIn("@ai-proposed", self.proposed.read_text())  # never promoted automatically

    def test_pipeline_withholds_unpromoted_instead_of_refusing(self):
        code, out = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 3, out)  # previously exit 1, nothing run
        self.assertNotIn("proposed.test.js", (self.r.root / "seen-api.txt").read_text())
        self.assertIn("reviewed.test.js", (self.r.root / "seen-api.txt").read_text())
        self.assertTrue(self.proposed.is_file(), "withheld file must be restored")
        cov = {c["id"]: c["status"] for c in self.r.json("evidence.json")["coverage"]}
        self.assertEqual(cov["AC-2"], "blocked")
        self.assertEqual(cov["AC-1"], "pass")

    def test_withheld_file_is_restored_even_when_the_suite_fails(self):
        self.r.test_file("api", "reviewed.test.js", ["TEST DEMO-1 AC-1 x | fail | boom"])
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 4)
        self.assertTrue(self.proposed.is_file())

    def test_interrupted_run_is_recovered_on_the_next_run(self):
        cfg = self.r.config()
        run_dir = self.r.root / "verification/DEMO-1/runs/OLD"
        run_dir.mkdir(parents=True)
        runner._withhold(self.r.root, run_dir, ["tests/api/proposed.test.js"])
        self.assertFalse(self.proposed.exists())
        with redirect_stdout(io.StringIO()):
            runner._recover(cfg, "DEMO-1")
        self.assertTrue(self.proposed.is_file())

    def test_restore_never_overwrites(self):
        run_dir = self.r.root / "verification/DEMO-1/runs/OLD"
        run_dir.mkdir(parents=True)
        runner._withhold(self.r.root, run_dir, ["tests/api/proposed.test.js"])
        self.proposed.write_text("someone wrote a new file here")
        problems = runner.restore_withheld(self.r.root, run_dir)
        self.assertEqual(len(problems), 1)
        self.assertEqual(self.proposed.read_text(), "someone wrote a new file here")
        self.assertTrue((run_dir / "withheld/tests/api/proposed.test.js").is_file())

    def test_unpromoted_evidence_never_reaches_verified(self):
        # Even if every test passes interactively, unreviewed evidence cannot verify.
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "interactive")
        self.assertEqual(code, 3)

    def test_marker_text_outside_suite_test_paths_is_not_pending_promotion(self):
        with redirect_stdout(io.StringIO()):
            self.r.cli("promote", "tests/api/proposed.test.js", "--by", "Reviewer", "--story", "DEMO-1")
        docs = self.r.root / "docs" / "example.test.js"
        docs.parent.mkdir()
        docs.write_text("// @ai-proposed DEMO-1 (an example in documentation)\n")
        code, out = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(self.r.cli("proposed")[1])["ai_proposed"], [])

    def test_promoted_tests_reach_verified_in_pipeline(self):
        with redirect_stdout(io.StringIO()):
            self.r.cli("promote", "tests/api/proposed.test.js", "--by", "Reviewer", "--story", "DEMO-1")
        code, out = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 0, out)

    def test_pipeline_does_not_read_stdin(self):
        s = Repo.suite("api")
        (self.r.root / "stdin_check.py").write_text("import sys\nsys.exit(0 if sys.stdin.read() == '' else 1)\n")
        s["command"] = "python3 stdin_check.py"
        s["junit"] = []
        self.r.cfg["suites"] = {"api": s}
        self.r.write_config()
        # Hold the engine's stdin open, like an unattended runner. If a suite inherited it,
        # it would wait forever; with stdin closed for suites it finishes at once.
        proc = subprocess.Popen([sys.executable, str(ROOT / ".claude/skills/verify-feature/scripts/verify.py"),
                                 "run", "DEMO-1", "--mode", "pipeline"], cwd=self.r.root,
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.assertEqual(proc.wait(timeout=30), 0)
        finally:
            proc.kill()
            proc.stdin.close()
        run_id = (self.r.root / "verification/DEMO-1/runs/LATEST").read_text().strip()
        m = json.loads((self.r.root / f"verification/DEMO-1/runs/{run_id}/run.json").read_text())
        self.assertEqual(m["suites"][0]["exit_code"], 0)


# ---------------------------------------------------------------- SC-07: blocked operations


class BlockedOperations(RepoTest):
    def setUp(self):
        super().setUp()
        self.r.gate1(a1="answered")
        self.r.plan([ac(1), ac(2, ("e2e",)), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-3 x | pass"])
        self.r.test_file("e2e", "b.test.js", ["TEST DEMO-1 AC-2 x | pass"])

    def _block_e2e(self, **change):
        self.r.cfg["suites"]["e2e"].update(change)
        self.r.write_config()
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        ev = self.r.json("evidence.json")
        return code, ev

    def assert_blocked_but_rest_ran(self, code, ev, words):
        self.assertEqual(code, 3)  # INCOMPLETE, never NOT VERIFIED or VERIFIED
        self.assertEqual(ev["suites"]["e2e"]["status"], "blocked")
        self.assertIn(words, ev["suites"]["e2e"]["reason"])
        self.assertEqual(ev["suites"]["api"]["status"], "ran")
        cov = {c["id"]: c["status"] for c in ev["coverage"]}
        self.assertEqual(cov, {"AC-1": "pass", "AC-2": "blocked", "AC-3": "pass"})
        self.assertFalse((self.r.root / "seen-e2e.txt").exists(), "a blocked suite must not execute")

    def test_command_not_allow_listed(self):
        code, ev = self._block_e2e(command="curl https://example.com")
        self.assert_blocked_but_rest_ran(code, ev, "allowed_commands")

    def test_shell_chaining(self):
        code, ev = self._block_e2e(command="python3 emit.py e2e reports/e2e.xml && rm -rf /")
        self.assert_blocked_but_rest_ran(code, ev, "shell syntax")

    def test_suite_env_pointing_at_production(self):
        code, ev = self._block_e2e(env={"BASE_URL": "https://shop.production.example.com"})
        self.assert_blocked_but_rest_ran(code, ev, "production")

    def test_shared_data_writes_need_explicit_permission(self):
        self.r.cfg["suites"]["e2e"]["writes_shared_data"] = True
        self.r.write_config()
        self.r.cli("all", "DEMO-1", "--mode", "pipeline", "--env", "uat")
        ev = self.r.json("evidence.json")
        self.assertEqual(ev["suites"]["e2e"]["status"], "blocked")
        self.assertIn("allow_shared_data_writes", ev["suites"]["e2e"]["reason"])
        # local allows it explicitly
        self.r.cli("all", "DEMO-1", "--mode", "pipeline", "--env", "local")
        self.assertEqual(self.r.json("evidence.json")["suites"]["e2e"]["status"], "ran")

    def test_production_environment_still_refuses_the_whole_run(self):
        self.r.cfg["environments"]["prod"] = {"BASE_URL": "https://prod.example.com"}
        self.r.cfg["guardrails"]["deny_url_patterns"] = [r"(^|[./-])prod([./-]|$)"]
        self.r.write_config()
        import contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.r.cli("run", "DEMO-1", "--env", "prod")
        self.assertEqual(code, 1)
        self.assertFalse((self.r.root / "seen-api.txt").exists())

    def test_missing_tool_is_not_started_not_failed(self):
        self.r.cfg["guardrails"]["allowed_commands"].append("no-such-tool-xyz")
        self.r.cfg["suites"]["e2e"]["command"] = "no-such-tool-xyz run"
        self.r.write_config()
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        ev = self.r.json("evidence.json")
        self.assertEqual(ev["suites"]["e2e"]["status"], "not-started")
        self.assertFalse(ev["suites"]["e2e"]["error"])
        self.assertEqual(code, 3)

    def test_report_distinguishes_pass_fail_skip_blocked_unresolved(self):
        self.r.gate1(a1="")
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-3 x | skip"])
        self._block_e2e(command="curl x")
        md = (self.r.root / "verification/DEMO-1/VERIFICATION_REPORT.md").read_text()
        for word in ("**PASS**", "**UNRESOLVED**", "BLOCKED", "1 passed", "1 skipped", "Open questions"):
            self.assertIn(word, md)
        rep = self.r.json("report.json")
        self.assertEqual(rep["tests"], {"passed": 1, "failed": 0, "skipped": 1, "suites_not_run": ["e2e"]})


# ---------------------------------------------------------------- 3.7: developer-facing findings


class Findings(RepoTest):
    def setUp(self):
        super().setUp()
        self.r.gate1(a1="answered")
        self.r.plan([ac(1), ac(2), ac(3)])

    def test_failure_finding_has_what_a_developer_needs(self):
        os.environ["SHOP_API_TOKEN"] = "tok-123456789"
        try:
            self.r.test_file("api", "a.test.js", [
                "TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass",
                "TEST DEMO-1 AC-3 bad code | fail | Error: wrong total\\n Expected: 108\\n Received: 120"
                "\\n Authorization: Bearer abcdefghijklmnop\\n token was tok-123456789",
            ])
            code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        finally:
            del os.environ["SHOP_API_TOKEN"]
        self.assertEqual(code, 4)
        f = self.r.json("findings.json")["findings"][0]
        self.assertEqual(f["story"], "DEMO-1")
        self.assertEqual(f["acceptance_criteria"], ["AC-3"])
        self.assertEqual(f["test"], "DEMO-1 AC-3 bad code")
        self.assertEqual((f["expected"], f["observed"]), ("108", "120"))
        self.assertEqual(f["classification"], "confirmed failure")
        for k in ("environment", "revision", "timestamp", "reproduce", "log"):
            self.assertTrue(f[k], k)
        self.assertIn("python3 emit.py api", f["reproduce"]["suite_command"])
        for secret in ("abcdefghijklmnop", "tok-123456789"):
            self.assertNotIn(secret, json.dumps(f))
            self.assertNotIn(secret, (self.r.root / "verification/DEMO-1/evidence.json").read_text())

    def test_unreviewed_failure_is_suspected_not_confirmed(self):
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass"])
        self.r.test_file("api", "p.test.js", ["TEST DEMO-1 AC-3 new | fail | nope"], proposed=True)
        self.r.cli("all", "DEMO-1", "--mode", "interactive")
        f = self.r.json("findings.json")["findings"]
        self.assertEqual([x["classification"] for x in f], ["suspected defect (unreviewed test)"])

    def test_unknown_origin_is_treated_as_unreviewed(self):
        # node:test style: JUnit does not name the file, and an unpromoted file ran in the suite.
        self.r.cfg["suites"]["api"]["command"] += " --no-file"
        self.r.write_config()
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | fail | e"])
        self.r.test_file("api", "p.test.js", ["TEST DEMO-1 AC-3 y | pass"], proposed=True)
        self.r.cli("all", "DEMO-1", "--mode", "interactive")
        ev = self.r.json("evidence.json")
        self.assertEqual({c["origin"] for c in ev["cases"]}, {"unknown"})
        f = self.r.json("findings.json")["findings"]
        self.assertEqual(f[0]["classification"], "suspected defect (unreviewed test)")

    def test_expected_and_observed_are_never_invented(self):
        self.assertEqual(report.expected_observed("something went wrong"), (None, None))
        self.assertEqual(report.expected_observed("Expected values to be strictly equal:\n\n120 !== 108\n"),
                         ("108", "120"))
        self.assertEqual(report.expected_observed('Expected string: "$108.00"\nReceived string: "$120.00"'),
                         ('"$108.00"', '"$120.00"'))
        # Real node:test output: a heading ending in ':' and an object dump with trailing commas.
        node = ("[Error [ERR_TEST_FAILURE]: Expected values to be strictly equal:\n\n108 !== 100\n] {\n"
                "  generatedMessage: true,\n  actual: 108,\n  expected: 100,\n  operator: 'strictEqual'\n}")
        self.assertEqual(report.expected_observed(node), ("100", "108"))
        self.assertEqual(report.expected_observed("Expected values to be equal:\n\nsomething"), (None, None))

    def test_suite_that_errors_without_results_stays_not_verified(self):
        (self.r.root / "crash.py").write_text("raise SystemExit(2)\n")
        self.r.cfg["suites"]["api"]["command"] = "python3 crash.py"
        self.r.write_config()
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 4)
        f = self.r.json("findings.json")["findings"]
        self.assertEqual(f[0]["kind"], "execution")


# ---------------------------------------------------------------- governance: working tree


class WorkingTree(RepoTest):
    def setUp(self):
        super().setUp()
        self.r.gate1(a1="answered")
        self.r.plan([ac(1), ac(2), ac(3)])
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass",
                                        "TEST DEMO-1 AC-3 x | pass"])
        (self.r.root / "app").mkdir()
        (self.r.root / "app" / "main.py").write_text("print('v1')\n")
        (self.r.root / ".gitignore").write_text("reports/\nseen-*\nverification/*/runs/\n")
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q"], cwd=self.r.root, check=True)
        subprocess.run(g + ["add", "-A"], cwd=self.r.root, check=True)
        subprocess.run(g + ["commit", "-qm", "init"], cwd=self.r.root, check=True)

    def test_clean_tree_verifies(self):
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 0)
        self.assertTrue(self.r.json("evidence.json")["working_tree"]["clean"])

    def test_uncommitted_application_change_cannot_verify_in_pipeline(self):
        (self.r.root / "app" / "main.py").write_text("print('patched to pass')\n")
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 3)
        self.assertIn("app/main.py", self.r.json("evidence.json")["working_tree"]["protected_source_changed"])

    def test_edited_reviewed_test_is_flagged(self):
        self.r.test_file("api", "a.test.js", ["TEST DEMO-1 AC-1 x | pass", "TEST DEMO-1 AC-2 x | pass",
                                        "TEST DEMO-1 AC-3 x | pass", "// loosened"])
        code, _ = self.r.cli("all", "DEMO-1", "--mode", "pipeline")
        self.assertEqual(code, 3)
        self.assertEqual(self.r.json("evidence.json")["working_tree"]["committed_tests_changed"], ["tests/api/a.test.js"])


# ---------------------------------------------------------------- SC-10: compatibility


class Compatibility(unittest.TestCase):
    def test_exit_codes_unchanged(self):
        self.assertEqual(verify.VERDICT_EXIT, {"VERIFIED": 0, "INCOMPLETE": 3, "NOT VERIFIED": 4})

    def test_old_evidence_shape_still_gets_a_verdict(self):
        old = {"mode": "pipeline", "suites": {"api": {"error": False}},
               "coverage": [{"id": "AC-1", "status": "pass"}], "regression": {"failed": []}}
        self.assertEqual(report.verdict(old, True, [], [])[0], "VERIFIED")

    def test_redaction(self):
        env = {"MY_PASSWORD": "hunter2-secret"}
        text = "pw=hunter2-secret url=/x?access_token=abc123&ok=1 Authorization: Basic dXNlcjpwYXNzd29yZA== password: 'p4ssw0rd'"
        out = redact(text, env)
        for s in ("hunter2-secret", "abc123", "dXNlcjpwYXNzd29yZA==", "p4ssw0rd"):
            self.assertNotIn(s, out)
        self.assertIn("ok=1", out)


if __name__ == "__main__":
    unittest.main()
