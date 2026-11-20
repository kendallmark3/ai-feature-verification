"""Inventory the repository's own test frameworks and tests.

Detection is by marker files only, so the result is the same on every run.
Nothing is installed or executed here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .util import out_dir, rel, write_json

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "target", ".venv", "venv", "__pycache__",
    "reports", "verification", ".next", "coverage", "test-results", "playwright-report", ".gradle",
}

TEST_FILE = re.compile(
    r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^test_.*\.py$)|(_test\.py$)|(_test\.go$)"
    r"|(Tests?\.java$)|(Tests?\.kt$)|(Tests?\.cs$)|(\.feature$)|(_spec\.rb$)"
)
AC_TAG = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)?[\s\[\]:/@]*\b(AC-\d+)\b")
PROPOSED = re.compile(r"@ai-proposed\b")
APPROVED = re.compile(r"@approved-by\b")

# (framework, marker test) pairs. Each marker is a path glob or a package.json dependency.
NPM_FRAMEWORKS = {
    "@playwright/test": "playwright",
    "jest": "jest",
    "vitest": "vitest",
    "cypress": "cypress",
    "mocha": "mocha",
    "@cucumber/cucumber": "cucumber-js",
}
FILE_MARKERS = [
    ("pytest", ["pytest.ini", "conftest.py", "tox.ini"]),
    ("maven-surefire", ["pom.xml"]),
    ("gradle-test", ["build.gradle", "build.gradle.kts"]),
    ("go-test", ["go.mod"]),
    ("cargo-test", ["Cargo.toml"]),
    ("dotnet-test", ["*.csproj", "*.sln"]),
    ("playwright", ["playwright.config.*"]),
    ("cypress", ["cypress.config.*"]),
]


def _walk(root: Path):
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def detect_frameworks(root: Path) -> list[dict]:
    found: dict[tuple[str, str], dict] = {}
    for p in _walk(root):
        if p.name == "package.json" and p.is_file():
            try:
                pkg = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            where = rel(p.parent, root) or "."
            for dep, name in NPM_FRAMEWORKS.items():
                if dep in deps:
                    found[(name, where)] = {"framework": name, "where": where, "marker": f"package.json:{dep}"}
            if any("node --test" in s for s in pkg.get("scripts", {}).values()):
                found[("node-test", where)] = {"framework": "node-test", "where": where, "marker": "package.json:scripts"}
            if pkg.get("scripts"):
                found.setdefault(("npm-scripts", where), {
                    "framework": "npm-scripts", "where": where, "marker": "package.json",
                    "scripts": {k: v for k, v in pkg["scripts"].items() if "test" in k},
                })
        elif p.is_file():
            for name, globs in FILE_MARKERS:
                if any(p.match(g) for g in globs):
                    where = rel(p.parent, root) or "."
                    found.setdefault((name, where), {"framework": name, "where": where, "marker": p.name})
        if p.name == "pyproject.toml" and p.is_file() and "[tool.pytest" in p.read_text(encoding="utf-8", errors="ignore"):
            where = rel(p.parent, root) or "."
            found.setdefault(("pytest", where), {"framework": "pytest", "where": where, "marker": "pyproject.toml"})
    return sorted(found.values(), key=lambda f: (f["where"], f["framework"]))


def scan_tests(root: Path) -> list[dict]:
    tests = []
    for p in _walk(root):
        if not p.is_file() or not TEST_FILE.search(p.name):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        tags = sorted({(m.group(1) or "") + ("/" if m.group(1) else "") + m.group(2) for m in AC_TAG.finditer(text)})
        tests.append({
            "path": rel(p, root),
            "ac_tags": tags,
            "ai_proposed": bool(PROPOSED.search(text)),
            "approved": bool(APPROVED.search(text)),
        })
    return tests


def inspect(cfg: dict, key: str | None = None) -> dict:
    root = Path(cfg["_root"])
    suites = cfg.get("suites", {})
    inv = {
        "frameworks": detect_frameworks(root),
        "configured_suites": {n: {"command": s.get("command"), "cwd": s.get("cwd", ".")} for n, s in suites.items()},
        "tests": scan_tests(root),
    }
    inv["summary"] = {
        "test_files": len(inv["tests"]),
        "files_with_ac_tags": sum(1 for t in inv["tests"] if t["ac_tags"]),
        "ai_proposed_unapproved": [t["path"] for t in inv["tests"] if t["ai_proposed"]],
        "unconfigured_frameworks": sorted(
            {f["framework"] for f in inv["frameworks"] if f["framework"] != "npm-scripts"}
            - {s.get("framework") for s in suites.values()}
        ),
    }
    if key:
        write_json(out_dir(cfg, key) / "repo-inventory.json", inv)
    return inv
