"""Create a starter verify.config.json from the frameworks found in the repo."""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import scaffold
from .inspect_repo import detect_frameworks
from .util import CONFIG_NAME, VerifyError

# Suggested commands that emit JUnit XML. A person must review them.
SUGGEST = {
    "playwright": ("npx playwright test --reporter=junit", ["test-results/junit.xml"],
                   {"PLAYWRIGHT_JUNIT_OUTPUT_NAME": "test-results/junit.xml"}),
    "jest": ("npx jest --ci --reporters=default --reporters=jest-junit", ["junit.xml"], {}),
    "vitest": ("npx vitest run --reporter=default --reporter=junit --outputFile=reports/vitest-junit.xml",
               ["reports/vitest-junit.xml"], {}),
    "cypress": ("npx cypress run --reporter junit --reporter-options mochaFile=reports/cypress-[hash].xml",
                ["reports/cypress-*.xml"], {}),
    "pytest": ("pytest --junitxml=reports/pytest-junit.xml", ["reports/pytest-junit.xml"], {}),
    "maven-surefire": ("mvn -B test", ["target/surefire-reports/TEST-*.xml"], {}),
    "gradle-test": ("gradle test", ["build/test-results/test/*.xml"], {}),
    "go-test": ("gotestsum --junitfile reports/go-junit.xml", ["reports/go-junit.xml"], {}),
    "dotnet-test": ("dotnet test --logger junit", ["**/TestResults/TestResults.xml"], {}),
}


def init(root: Path, force: bool = False) -> Path:
    path = root / CONFIG_NAME
    if path.exists() and not force:
        raise VerifyError(f"{path} already exists. Use --force to replace it.")
    suites = {}
    for f in detect_frameworks(root):
        if f["framework"] not in SUGGEST:
            continue
        cmd, junit, env = SUGGEST[f["framework"]]
        name = f["framework"] if f["where"] == "." else f"{f['framework']}:{f['where']}"
        suites[name] = {"framework": f["framework"], "cwd": f["where"], "command": cmd, "junit": junit,
                        "artifacts": [], "env": env, "test_paths": [f["where"]], "_review": "Suggested. Confirm before use."}
        if f["framework"] == "maven-surefire" and not scaffold.maven_tags_kept(root / f["where"] / "pom.xml"):
            suites[name]["_review"] += (" pom.xml lacks usePhrasedTestCaseMethodName=true: @DisplayName AC tags "
                                        "will be lost. See the ACTION NEEDED note from init, or ac-tagging.md.")
    cfg = {
        "output_dir": "verification",
        "jira": jira_block(),
        "environments": {"local": {"BASE_URL": "", "allow_shared_data_writes": True},
                         "dev": {"BASE_URL": "${DEV_BASE_URL}"}},
        "guardrails": {"allowed_commands": ["npm", "npx", "node", "pytest", "python3", "mvn", "gradle", "./gradlew",
                                            "go", "gotestsum", "dotnet"],
                       "deny_url_patterns": ["(^|[./-])prod([./-]|$)", "production"],
                       "protected_paths": [],
                       "max_runtime_seconds": 900},
        "suites": suites,
    }
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path


def review_notes(root: Path) -> list[str]:
    """What the person must decide before every criterion can be traced. init changes no build file."""
    notes = []
    for n in scaffold.needs(root):
        if n["framework"] == "maven-surefire":
            notes.append(f"{n['where']}/pom.xml: JUnit 5 @DisplayName tags (e.g. \"SAT-1 AC-1 ...\") will not reach "
                         "Surefire's XML, so those tests would count as untagged. Add this to <build><plugins> "
                         "(Surefire 3.0.0-M4+), or let `verify.py frameworks <KEY> --propose` add it after a person "
                         "approves:\n" + scaffold.MAVEN_REPORTER_SNIPPET)
        else:
            default = "Playwright" if n["framework"] == "playwright" else "pytest"
            notes.append(f"{n['where']}: {n['why']}. The default is {default}. Nothing is added until a named person "
                         "approves: `verify.py frameworks <KEY> --propose`, then `--approve --by \"Name\"`, then `--apply`.")
    return notes


CLOUD_JIRA = {"adapter": "cloud", "base_url": "${JIRA_BASE_URL}", "email": "${JIRA_EMAIL}",
              "api_token": "${JIRA_API_TOKEN}"}


def jira_block(environ: dict | None = None) -> dict:
    """Real Jira when JIRA_BASE_URL is set in the environment, otherwise simulated stories in jira/.

    Only ${VAR} references are written: the URL, email and token stay in the environment.
    """
    env = os.environ if environ is None else environ
    return dict(CLOUD_JIRA) if env.get("JIRA_BASE_URL") else {"adapter": "local", "path": "jira"}
