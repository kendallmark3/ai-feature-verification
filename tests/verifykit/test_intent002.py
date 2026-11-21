"""INTENT-002: real Jira (REST v2) and plugin packaging. Standard library only."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/verify-feature/scripts"))

from verifykit import config_init, evidence, plan, runner, story  # noqa: E402
from verifykit.util import VerifyError, verify_cmd  # noqa: E402


class WikiMarkupCriteria(unittest.TestCase):
    def acs(self, desc):
        return [a["text"] for a in story.parse_acceptance_criteria(story._ac_block_from_description(desc))]

    def test_numbered_wiki_list_under_h2(self):
        self.assertEqual(self.acs("Intro\nh2. Acceptance Criteria\n# One\n# Two\nh2. Notes\n# not an AC"), ["One", "Two"])

    def test_bulleted_wiki_list(self):
        self.assertEqual(self.acs("h3. Acceptance Criteria:\n* One\n* Two"), ["One", "Two"])

    def test_wiki_continuation_line_joins_previous(self):
        self.assertEqual(self.acs("h2. Acceptance Criteria\n# Shows a total\nincluding tax"), ["Shows a total including tax"])

    def test_markdown_still_stops_at_next_heading(self):
        self.assertEqual(self.acs("## Acceptance Criteria\n1. One\n2. Two\n## Notes\n- not an AC"), ["One", "Two"])


class NoCriteriaStopsTheLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "jira").mkdir()
        (root / "jira" / "EMP-1.json").write_text(json.dumps({"key": "EMP-1", "summary": "s", "description": ""}))
        self.cfg = {"_root": str(root), "output_dir": "verification", "jira": {"adapter": "local", "path": "jira"},
                    "suites": {"s": {"command": "python3 -c pass"}}}
        story.pull(self.cfg, "EMP-1")

    def tearDown(self):
        self.tmp.cleanup()

    def test_plan_check_reports_a_problem(self):
        plan.init(self.cfg, "EMP-1")
        self.assertTrue(any("no acceptance criteria" in p for p in plan.validate(self.cfg, "EMP-1")))

    def test_run_refuses_before_any_suite(self):
        with self.assertRaisesRegex(VerifyError, "no acceptance criteria"):
            runner.run(self.cfg, "EMP-1", [], "interactive", "local")

    def test_run_refuses_when_the_story_was_never_pulled(self):
        with self.assertRaisesRegex(VerifyError, "not pulled"):
            runner.run(self.cfg, "NEVER-1", [], "interactive", "local")


class ClassNameTags(unittest.TestCase):
    def test_class_name_forms(self):
        for classname in ("tests.TestSHOP142_AC2", "TestAC2", "Test_AC_2", "Spec.AC-2"):
            self.assertEqual(evidence._tags({"name": "t", "classname": classname}, "SHOP-142"), ["AC-2"], classname)

    def test_several_and_multi_digit(self):
        self.assertEqual(evidence._tags({"name": "t", "classname": "TestX_AC2_AC12"}, "X-1"), ["AC-12", "AC-2"])

    def test_letters_before_ac_are_not_a_tag(self):
        self.assertEqual(evidence._tags({"name": "test_vac1 TRAC2 MAC3", "classname": "c"}, "X-1"), [])


class InitPicksTheJiraAdapter(unittest.TestCase):
    def test_cloud_when_jira_base_url_is_set(self):
        block = config_init.jira_block({"JIRA_BASE_URL": "https://x.atlassian.net"})
        self.assertEqual(block["adapter"], "cloud")
        self.assertEqual(block["api_token"], "${JIRA_API_TOKEN}")  # a reference, never the value

    def test_local_otherwise(self):
        self.assertEqual(config_init.jira_block({}), {"adapter": "local", "path": "jira"})


class PluginPackaging(unittest.TestCase):
    def test_engine_command_is_relative_inside_the_repo(self):
        self.assertEqual(verify_cmd(ROOT), "python3 .claude/skills/verify-feature/scripts/verify.py")

    def test_engine_command_uses_the_plugin_root_elsewhere(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/verify-feature/scripts/verify.py", verify_cmd(d))

    def test_marketplace_points_at_a_plugin_with_the_three_skills(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        entry = next(p for p in market["plugins"] if p["name"] == "ai-feature-verification")
        plugin_root = (ROOT / entry["source"]).resolve()
        manifest = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "ai-feature-verification")
        for skill in ("verify-feature", "clarify-story", "promote-tests"):
            self.assertTrue((plugin_root / "skills" / skill / "SKILL.md").is_file(), skill)

    def test_skills_do_not_hard_code_the_repo_path(self):
        for md in (ROOT / ".claude" / "skills").glob("*/SKILL.md"):
            self.assertNotIn(".claude/skills/verify-feature/scripts/verify.py", md.read_text(), md)


if __name__ == "__main__":
    unittest.main()
