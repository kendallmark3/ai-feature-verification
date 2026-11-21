"""INTENT-003: Saturday-ready (Spring Boot + React). Standard library only."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/skills/verify-feature/scripts"))

import verify  # noqa: E402
from verifykit import config_init, evidence, scaffold  # noqa: E402
from verifykit.util import VerifyError  # noqa: E402

# A fresh Spring Initializr pom and a fresh Vite React package.json: no reporter, no front-end tests.
RAW = ROOT / "tests/verifykit/fixtures/saturday-raw"
PHRASED = ("<project><build><plugins><plugin><artifactId>maven-surefire-plugin</artifactId><configuration>"
           "<statelessTestsetReporter><usePhrasedTestCaseMethodName>true</usePhrasedTestCaseMethodName>"
           "</statelessTestsetReporter></configuration></plugin></plugins></build></project>")


def copy_starter(dest: Path) -> Path:
    shutil.copytree(RAW, dest)
    return dest


class StarterRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = copy_starter(Path(self.tmp.name) / "repo")
        self.pom_before = (self.root / "backend/pom.xml").read_text()
        self.pkg_before = (self.root / "frontend/package.json").read_text()

    def tearDown(self):
        self.tmp.cleanup()

    def cfg(self):
        return {"_root": str(self.root), "output_dir": "verification", "suites": {}}


class InitFindsBothApps(StarterRepo):
    def test_nested_backend_suite_with_cwd_and_junit(self):
        config_init.init(self.root)
        suites = json.loads((self.root / "verify.config.json").read_text())["suites"]
        self.assertIn("maven-surefire:backend", suites)
        s = suites["maven-surefire:backend"]
        self.assertEqual((s["cwd"], s["command"], s["junit"]), ("backend", "mvn -B test", ["target/surefire-reports/TEST-*.xml"]))
        self.assertIn("usePhrasedTestCaseMethodName", s["_review"])

    def test_front_end_without_tests_gets_no_suite_only_a_note(self):
        config_init.init(self.root)
        suites = json.loads((self.root / "verify.config.json").read_text())["suites"]
        self.assertFalse([n for n in suites if "frontend" in n])
        notes = config_init.review_notes(self.root)
        self.assertTrue(any(n.startswith("frontend:") and "Playwright" in n and "approves" in n for n in notes))
        self.assertTrue(any("backend/pom.xml" in n and "usePhrasedTestCaseMethodName" in n for n in notes))

    def test_init_changes_no_build_file_and_adds_no_framework(self):
        out = io.StringIO()
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out):
                self.assertEqual(verify.main(["init"]), 0)
        finally:
            os.chdir(cwd)
        self.assertIn("ACTION NEEDED", out.getvalue())
        self.assertEqual((self.root / "backend/pom.xml").read_text(), self.pom_before)
        self.assertEqual((self.root / "frontend/package.json").read_text(), self.pkg_before)
        self.assertFalse(list((self.root / "frontend").glob("playwright.config.*")))

    def test_init_with_phrased_reporter_has_no_maven_note(self):
        (self.root / "backend/pom.xml").write_text(PHRASED)
        self.assertFalse(any("pom.xml" in n for n in config_init.review_notes(self.root)))


class ProposeApproveApply(StarterRepo):
    def test_proposal_lists_files_and_dev_dependencies_and_writes_nothing(self):
        prop = scaffold.propose(self.cfg(), "SAT-0")
        ids = [i["id"] for i in prop["items"]]
        self.assertEqual(sorted(ids), ["maven-reporter:backend", "playwright:frontend"])
        pw = next(i for i in prop["items"] if i["framework"] == "playwright")
        self.assertIn("frontend/playwright.config.mjs", pw["creates"])
        self.assertEqual(pw["package_json"]["devDependencies"], {"@playwright/test": scaffold.PLAYWRIGHT_VERSION})
        config = pw["creates"]["frontend/playwright.config.mjs"]
        self.assertIn("spring-boot:run", config)        # starts the API ...
        self.assertIn("cwd: '../backend'", config)
        self.assertIn("npm run dev", config)            # ... and the UI
        self.assertIn("reports/e2e-junit.xml", config)
        self.assertIn("--port 5310 --strictPort", config)  # not Vite's 5173, where a dev server may run
        self.assertTrue((self.root / "verification/SAT-0/FRAMEWORK_PROPOSAL.md").is_file())
        self.assertEqual((self.root / "backend/pom.xml").read_text(), self.pom_before)
        self.assertEqual((self.root / "frontend/package.json").read_text(), self.pkg_before)

    def test_apply_refuses_without_approval(self):
        scaffold.propose(self.cfg(), "SAT-0")
        with self.assertRaisesRegex(VerifyError, "Not approved"):
            scaffold.apply(self.cfg(), "SAT-0")
        self.assertEqual((self.root / "backend/pom.xml").read_text(), self.pom_before)
        self.assertFalse((self.root / "frontend/playwright.config.mjs").exists())

    def test_approval_needs_a_name(self):
        scaffold.propose(self.cfg(), "SAT-0")
        with self.assertRaises(VerifyError):
            scaffold.approve(self.cfg(), "SAT-0", "  ")

    def test_cli_approve_needs_by(self):
        (self.root / "verify.config.json").write_text(json.dumps({"suites": {}}))
        cwd = os.getcwd()
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                verify.main(["frameworks", "SAT-0", "--propose"])
                self.assertEqual(verify.main(["frameworks", "SAT-0", "--approve"]), 1)
        finally:
            os.chdir(cwd)

    def test_approved_apply_records_name_and_makes_exactly_the_changes(self):
        (self.root / "verify.config.json").write_text(json.dumps({"suites": {}}))
        scaffold.propose(self.cfg(), "SAT-0")
        scaffold.approve(self.cfg(), "SAT-0", "Test Person")
        out = scaffold.apply(self.cfg(), "SAT-0")
        self.assertEqual(out["approved_by"], "Test Person")
        pom = (self.root / "backend/pom.xml").read_text()
        self.assertTrue(scaffold.maven_tags_kept(self.root / "backend/pom.xml"))
        self.assertIn("spring-boot-maven-plugin", pom)   # existing plugin kept
        self.assertLess(pom.index("spring-boot-maven-plugin"), pom.index("maven-surefire-plugin"))
        self.assertIn("      </plugin>\n      <plugin>\n        <groupId>org.apache.maven.plugins</groupId>", pom)
        pkg = json.loads((self.root / "frontend/package.json").read_text())
        self.assertEqual(pkg["devDependencies"]["@playwright/test"], scaffold.PLAYWRIGHT_VERSION)
        self.assertEqual(pkg["devDependencies"]["vite"], "^5.4.11")
        suites = json.loads((self.root / "verify.config.json").read_text())["suites"]
        self.assertEqual(suites["playwright:frontend"]["cwd"], "frontend")
        rec = json.loads((self.root / "verification/SAT-0/framework-proposal.json").read_text())
        self.assertEqual(rec["approval"]["by"], "Test Person")
        self.assertTrue(rec["approval"]["at"])
        self.assertIn("npm install", out["next"][0])
        self.assertFalse((self.root / "frontend/node_modules").exists())  # nothing installed
        with self.assertRaisesRegex(VerifyError, "Already applied"):
            scaffold.apply(self.cfg(), "SAT-0")
        self.assertEqual(scaffold.needs(self.root), [])  # nothing left to propose

    def test_editing_the_proposal_after_approval_voids_it(self):
        scaffold.propose(self.cfg(), "SAT-0")
        scaffold.approve(self.cfg(), "SAT-0", "Test Person")
        p = self.root / "verification/SAT-0/framework-proposal.json"
        rec = json.loads(p.read_text())
        rec["items"][0]["creates"] = {"evil.sh": "rm -rf /"}
        p.write_text(json.dumps(rec))
        with self.assertRaisesRegex(VerifyError, "changed after it was approved"):
            scaffold.apply(self.cfg(), "SAT-0")
        self.assertFalse((self.root / "evil.sh").exists())

    def test_apply_never_overwrites_an_existing_file(self):
        scaffold.propose(self.cfg(), "SAT-0")
        scaffold.approve(self.cfg(), "SAT-0", "Test Person")
        (self.root / "frontend/playwright.config.mjs").write_text("// the team's own\n")
        with self.assertRaisesRegex(VerifyError, "overwrite"):
            scaffold.apply(self.cfg(), "SAT-0")
        self.assertEqual((self.root / "backend/pom.xml").read_text(), self.pom_before)


class NeverASecondFramework(unittest.TestCase):
    def test_demo_app_and_this_repo_get_no_proposal(self):
        # The raw test fixture is deliberately untested; everything else here has its frameworks.
        fixture = "tests/verifykit/fixtures/"
        self.assertEqual([n for n in scaffold.needs(ROOT) if not n["where"].startswith(fixture)], [])

    def test_playwright_starts_the_nearest_backend(self):
        d = self.tmp({"a/backend/pom.xml": "<project>spring-boot</project>",
                      "b/backend/pom.xml": "<project>spring-boot</project>",
                      "b/frontend/package.json": json.dumps({"dependencies": {"react": "1"}})})
        item = next(i for i in scaffold.propose({"_root": str(d), "output_dir": "v"}, "K-1")["items"]
                    if i["framework"] == "playwright")
        self.assertIn("cwd: '../backend'", item["creates"]["b/frontend/playwright.config.mjs"])

    def tmp(self, files: dict) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        for name, text in files.items():
            (d / name).parent.mkdir(parents=True, exist_ok=True)
            (d / name).write_text(text)
        return d

    def test_front_end_with_vitest_or_jest_is_left_alone(self):
        for fw in ("vitest", "jest", "@playwright/test", "cypress"):
            d = self.tmp({"web/package.json": json.dumps({"dependencies": {"react": "1"}, "devDependencies": {fw: "1"}})})
            self.assertEqual(scaffold.needs(d), [], fw)

    def test_node_library_without_ui_is_not_a_web_front_end(self):
        d = self.tmp({"package.json": json.dumps({"dependencies": {"express": "4"}})})
        self.assertEqual(scaffold.needs(d), [])

    def test_python_without_pytest_gets_pytest_proposed(self):
        d = self.tmp({"svc/requirements.txt": "requests\n"})
        self.assertEqual([(n["framework"], n["where"]) for n in scaffold.needs(d)], [("pytest", "svc")])

    def test_python_with_pytest_is_left_alone(self):
        for files in ({"requirements.txt": "pytest\n"}, {"pyproject.toml": "[tool.pytest.ini_options]\n"},
                      {"pyproject.toml": "[project]\n", "conftest.py": ""}):
            self.assertEqual(scaffold.needs(self.tmp(files)), [], files)

    def test_pom_that_already_configures_surefire_is_hand_edit_only(self):
        d = self.tmp({"pom.xml": "<project><build><plugins><plugin><artifactId>maven-surefire-plugin</artifactId>"
                                 "</plugin></plugins></build></project>"})
        item = scaffold.propose({"_root": str(d), "output_dir": "verification"}, "K-1")["items"][0]
        self.assertIn("by hand", item["manual"])

    def test_pom_without_build_section_gets_one(self):
        text = scaffold._insert_reporter("<project>\n  <modelVersion>4.0.0</modelVersion>\n</project>\n")
        self.assertIn("<build>", text)
        self.assertTrue(scaffold.MAVEN_PHRASED_NAMES.search(text))


class JavaTagsReachTheEvidence(unittest.TestCase):
    """The two Surefire XML shapes measured on 2026-11-21 (Surefire 3.5.2, JUnit 5.11)."""

    def parse(self, xml: str):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        (d / "TEST-x.xml").write_text(xml)
        return [evidence._tags(c, "SAT-0") for c in evidence.parse_junit(d / "TEST-x.xml", "backend")]

    def test_default_reporter_loses_the_display_name(self):
        xml = ('<testsuite name="com.example.intake.IntakeApiTest"><testcase name="submitsValidIntake" '
               'classname="com.example.intake.IntakeApiTest" time="0.1"/></testsuite>')
        self.assertEqual(self.parse(xml), [[]])

    def test_phrased_reporter_carries_the_tag(self):
        xml = ('<testsuite name="IntakeApiTest"><testcase name="SAT-0 AC-1 valid intake returns 201 with a reference" '
               'classname="IntakeApiTest" time="0.1"/></testsuite>')
        self.assertEqual(self.parse(xml), [["AC-1"]])


class JavaOrigin(unittest.TestCase):
    UNPROMOTED = ["backend/src/test/java/com/example/intake/IntakeApiTest.java"]

    def origin(self, classname, framework="maven-surefire"):
        return evidence._origin({"classname": classname},
                                {"framework": framework, "unpromoted": self.UNPROMOTED})

    def test_ai_proposed_java_class_is_unpromoted(self):
        self.assertEqual(self.origin("com.example.intake.IntakeApiTest"), "unpromoted")
        self.assertEqual(self.origin("com.example.intake.IntakeApiTest$Nested"), "unpromoted")

    def test_reviewed_java_class_is_committed(self):
        self.assertEqual(self.origin("com.example.intake.IntakeApplicationTests"), "committed")

    def test_dotted_classname_outside_jvm_suites_stays_unknown(self):
        self.assertEqual(self.origin("tests.ids3.test_live", framework="pytest"), "unknown")


class SaturdayDocs(unittest.TestCase):
    REF = ROOT / ".claude/skills/verify-feature/references"

    def test_ac_tagging_warns_about_surefire(self):
        self.assertIn("usePhrasedTestCaseMethodName", (self.REF / "ac-tagging.md").read_text())

    def test_framework_adapters_covers_defaults_and_small_gaps(self):
        text = (self.REF / "framework-adapters.md").read_text()
        for needle in ("frameworks SAT-1 --propose", "jest-junit", "Mocha", "unittest", "usePhrasedTestCaseMethodName"):
            self.assertIn(needle, text)

    def test_story_template_exists(self):
        self.assertIn("Acceptance Criteria", (self.REF / "story-template.md").read_text())


if __name__ == "__main__":
    unittest.main()
