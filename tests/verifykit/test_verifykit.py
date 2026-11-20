"""Unit tests for verifykit. Standard library only:

    python3 -m unittest discover -s tests/verifykit -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/verify-feature/scripts"))

from verifykit import evidence, gaps, guardrails, report, story  # noqa: E402
from verifykit.util import VerifyError  # noqa: E402


class StoryParsing(unittest.TestCase):
    def test_list_items_become_separate_acs(self):
        acs = story.parse_acceptance_criteria(story._lines_from(["Can log in", "Bad password shows an error"]))
        self.assertEqual([a["id"] for a in acs], ["AC-1", "AC-2"])

    def test_explicit_ids_are_kept_and_numbering_skips_them(self):
        acs = story.parse_acceptance_criteria(["AC-2: second", "- first unnamed"])
        self.assertEqual([(a["id"], a["text"]) for a in acs], [("AC-2", "second"), ("AC-1", "first unnamed")])

    def test_continuation_lines_join_previous(self):
        acs = story.parse_acceptance_criteria(["1. Shows a total", "   including tax"])
        self.assertEqual(acs[0]["text"], "Shows a total including tax")

    def test_ac_block_from_description(self):
        desc = "Intro\n\nh3. Acceptance Criteria\n* One\n* Two\nh3. Notes\n* not an AC"
        self.assertEqual(len(story.parse_acceptance_criteria(story._ac_block_from_description(desc))), 2)


class GapRules(unittest.TestCase):
    def _rules(self, *acs):
        s = {"key": "X-1", "description": "d",
             "acceptance_criteria": [{"id": f"AC-{i+1}", "text": t} for i, t in enumerate(acs)]}
        return [(f["ac"], f["rule"]) for f in gaps.analyse(s)]

    def test_unmeasured_performance_is_flagged(self):
        self.assertIn(("AC-1", "UNMEASURED_NFR"), self._rules("Should be fast", "Bad input shows an error"))

    def test_measured_performance_is_not_flagged(self):
        r = self._rules("Search returns results in under 300 ms at p95", "Bad input shows an error")
        self.assertNotIn(("AC-1", "UNMEASURED_NFR"), r)

    def test_story_without_error_path(self):
        self.assertIn(("STORY", "NO_ERROR_PATH"), self._rules("Shows the total of 3 items", "Saves the cart"))

    def test_same_story_same_questions(self):
        s = {"key": "X-1", "description": "", "acceptance_criteria": [{"id": "AC-1", "text": "Works on mobile"}]}
        self.assertEqual(gaps.analyse(s), gaps.analyse(s))


class Guardrails(unittest.TestCase):
    def test_shell_syntax_refused(self):
        with self.assertRaises(VerifyError):
            guardrails.parse_command("npm test && rm -rf /", ["npm"])

    def test_unlisted_command_refused(self):
        with self.assertRaises(VerifyError):
            guardrails.parse_command("curl http://x", ["npm"])

    def test_prod_url_refused(self):
        for url in ("https://prod.shop.example.com", "https://shop-production.example.com"):
            with self.assertRaises(VerifyError):
                guardrails.check_target({"BASE_URL": url}, [])

    def test_uat_url_allowed(self):
        guardrails.check_target({"BASE_URL": "https://uat.shop.example.com"}, [])

    def test_literal_secret_refused(self):
        with self.assertRaises(VerifyError):
            guardrails.check_no_literal_secrets({"jira": {"api_token": "abc123"}})
        guardrails.check_no_literal_secrets({"jira": {"api_token": "${JIRA_API_TOKEN}"}})


class JUnitParsing(unittest.TestCase):
    XML = """<testsuites><testsuite name="s" hostname="mobile">
      <testcase name="SHOP-1 AC-2 applies code" classname="c" time="0.5">
        <system-out><![CDATA[[[ATTACHMENT|e2e-artifacts/x/test-finished-1.png]]]]></system-out></testcase>
      <testcase name="SHOP-1 AC-3 rejects code" classname="c" time="0.1"><failure message="expected 400"/></testcase>
      <testcase name="OTHER-9 AC-2 not ours" classname="c"/>
    </testsuite><testcase name="node style" failure="boom"/></testsuites>"""

    def test_parse_and_tag(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "j.xml"
            p.write_text(self.XML)
            cases = evidence.parse_junit(p, "e2e")
        self.assertEqual([c["status"] for c in cases], ["pass", "fail", "pass", "fail"])
        self.assertEqual(cases[0]["project"], "mobile")
        self.assertEqual(cases[0]["attachments"], ["e2e-artifacts/x/test-finished-1.png"])
        self.assertEqual(evidence._tags(cases[0], "SHOP-1"), ["AC-2"])
        self.assertEqual(evidence._tags(cases[2], "SHOP-1"), [])


class Verdict(unittest.TestCase):
    def _ev(self, statuses, mode="pipeline", regression_failed=()):
        return {"mode": mode, "suites": {"api": {"error": False}},
                "coverage": [{"id": f"AC-{i}", "status": s} for i, s in enumerate(statuses, 1)],
                "regression": {"failed": list(regression_failed)}}

    def test_any_failure_is_not_verified(self):
        self.assertEqual(report.verdict(self._ev(["pass", "fail"]), True, [], [])[0], "NOT VERIFIED")

    def test_missing_coverage_is_incomplete(self):
        self.assertEqual(report.verdict(self._ev(["pass", "missing"]), True, [], [])[0], "INCOMPLETE")

    def test_interactive_mode_cannot_be_verified(self):
        self.assertEqual(report.verdict(self._ev(["pass"], mode="interactive"), True, [], [])[0], "INCOMPLETE")

    def test_all_green_in_pipeline_is_verified(self):
        self.assertEqual(report.verdict(self._ev(["pass", "pass"]), True, [], [])[0], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
