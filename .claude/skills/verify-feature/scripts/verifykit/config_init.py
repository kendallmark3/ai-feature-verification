"""Create a starter verify.config.json from the frameworks found in the repo."""
from __future__ import annotations

import json
from pathlib import Path

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
    cfg = {
        "output_dir": "verification",
        "jira": {"adapter": "local", "path": "jira"},
        "environments": {"local": {"BASE_URL": ""}, "dev": {"BASE_URL": "${DEV_BASE_URL}"}},
        "guardrails": {"allowed_commands": ["npm", "npx", "node", "pytest", "python3", "mvn", "gradle", "./gradlew",
                                            "go", "gotestsum", "dotnet"],
                       "deny_url_patterns": ["(^|[./-])prod([./-]|$)", "production"],
                       "max_runtime_seconds": 900},
        "suites": suites,
    }
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path
