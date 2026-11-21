"""Propose a default test framework (or a build-file fix) and apply it only after a person approves.

INTENT-003. The team's framework always wins. Only where a project has none is a default proposed:
Playwright for a web front end, pytest for Python. A Maven project whose Surefire drops JUnit 5
@DisplayName gets the reporter block that keeps AC tags. Every change is listed in
verification/<KEY>/framework-proposal.json; `apply` refuses until a named person has approved
that exact proposal. The engine never installs anything: it prints the install commands.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .inspect_repo import NPM_FRAMEWORKS, _walk
from .util import CONFIG_NAME, VerifyError, now_iso, out_dir, read_json, rel, write_json, write_text

PLAYWRIGHT_VERSION = "^1.65.1"
# Playwright starts the UI on its own port so a developer's `npm run dev` (Vite: 5173) or another
# local app can't collide with it, or be tested by mistake (the runner sets CI=1, so no reuse).
UI_TEST_PORT = 5310
PYTEST_REQUIREMENT = "pytest>=8"

# A package.json with one of these is a web front end.
WEB_DEPS = ("react", "react-dom", "vue", "svelte", "@angular/core", "next", "vite", "preact", "solid-js")
PY_PROJECT_FILES = ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg")
PY_PYTEST_FILES = ("pytest.ini", "conftest.py", "tox.ini")

# Maven Surefire writes a JUnit 5 test's method name to its XML, not its @DisplayName, so a
# "KEY AC-n" tag in @DisplayName is lost unless this reporter option is on (measured with
# Surefire 3.5.2 and JUnit 5.11; see INTENT-003).
MAVEN_PHRASED_NAMES = re.compile(r"<usePhrasedTestCaseMethodName>\s*true\s*</usePhrasedTestCaseMethodName>")
MAVEN_REPORTER_SNIPPET = """<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <statelessTestsetReporter implementation="org.apache.maven.plugin.surefire.extensions.junit5.JUnit5Xml30StatelessReporter">
      <usePhrasedTestCaseMethodName>true</usePhrasedTestCaseMethodName>
    </statelessTestsetReporter>
  </configuration>
</plugin>"""


def maven_tags_kept(pom: Path) -> bool:
    return bool(MAVEN_PHRASED_NAMES.search(pom.read_text(encoding="utf-8", errors="ignore")))


# ---------------------------------------------------------------- detection

def _has_test_framework_js(d: Path, pkg: dict) -> bool:
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    if any(dep in deps for dep in NPM_FRAMEWORKS):
        return True
    if any("node --test" in s for s in pkg.get("scripts", {}).values()):
        return True
    return any(d.glob("playwright.config.*")) or any(d.glob("cypress.config.*"))


def _has_pytest(d: Path) -> bool:
    if any((d / f).is_file() for f in PY_PYTEST_FILES):
        return True
    for f in ("pyproject.toml", "setup.cfg", *[p.name for p in d.glob("requirements*.txt")]):
        p = d / f
        if p.is_file() and re.search(r"(?im)^\s*\[tool\.pytest|^\s*\[tool:pytest\]|\bpytest\b", p.read_text(encoding="utf-8", errors="ignore")):
            return True
    return False


def needs(root: Path) -> list[dict]:
    """Where a default framework or a build-file fix would be proposed. Reads files only."""
    out, poms = [], []
    for p in _walk(root):
        if not p.is_file():
            continue
        d, where = p.parent, rel(p.parent, root) or "."
        if p.name == "package.json":
            try:
                pkg = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if any(dep in deps for dep in WEB_DEPS) and not _has_test_framework_js(d, pkg):
                out.append({"kind": "framework", "framework": "playwright", "where": where,
                            "why": "web front end with no test framework"})
        elif p.name in PY_PROJECT_FILES and not any(o["where"] == where and o["framework"] == "pytest" for o in out):
            if not _has_pytest(d) and not (d / "package.json").is_file():
                out.append({"kind": "framework", "framework": "pytest", "where": where,
                            "why": "Python project with no pytest configuration"})
        elif p.name == "pom.xml":
            poms.append(where)
            if not maven_tags_kept(p):
                out.append({"kind": "build-config", "framework": "maven-surefire", "where": where,
                            "why": "Surefire drops JUnit 5 @DisplayName, so 'KEY AC-n' tags would be lost"})
    for o in out:
        o["_poms"] = poms
    return out


# ---------------------------------------------------------------- proposal content

def _relpath(target: Path, start: Path) -> str:
    return Path(os.path.relpath(target, start)).as_posix()


def _playwright_item(root: Path, need: dict) -> dict:
    where = need["where"]
    d = root / where
    pkg = json.loads((d / "package.json").read_text(encoding="utf-8"))
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    scripts = pkg.get("scripts", {})
    if "vite" in deps or "dev" in scripts:
        ui = {"command": f"npm run dev -- --host 127.0.0.1 --port {UI_TEST_PORT} --strictPort", "port": UI_TEST_PORT}
    else:
        ui = {"command": f"PORT={UI_TEST_PORT} npm start", "port": UI_TEST_PORT}
    servers = []
    backend = None
    # The nearest Spring Boot project (a sibling `backend/` before one elsewhere in a larger repo).
    nearest = sorted(need.get("_poms", []), key=lambda w: (-len(Path(os.path.commonpath([root / w, d])).parts), w))
    for pw in nearest:
        pom = root / pw / "pom.xml"
        if "spring-boot" in pom.read_text(encoding="utf-8", errors="ignore"):
            port = 8080
            props = root / pw / "src/main/resources/application.properties"
            if props.is_file():
                m = re.search(r"(?m)^\s*server\.port\s*=\s*(\d+)", props.read_text(encoding="utf-8"))
                port = int(m.group(1)) if m else port
            backend = {"cwd": _relpath(root / pw, d), "port": port}
            break
    if backend:
        servers.append(f"    {{ command: 'mvn -B -q spring-boot:run', cwd: '{backend['cwd']}', port: {backend['port']}, "
                       "timeout: 180_000, reuseExistingServer: !process.env.CI },")
    servers.append(f"    {{ command: '{ui['command']}', url: 'http://127.0.0.1:{ui['port']}', "
                   "timeout: 60_000, reuseExistingServer: !process.env.CI },")
    config = "\n".join([
        "// Playwright for this front end, proposed by verify.py frameworks (INTENT-003).",
        "// BASE_URL points the suite at a running DEV/UAT host; without it Playwright starts",
        "// " + ("the API and the UI" if backend else "the UI") + " locally.",
        "import { defineConfig, devices } from '@playwright/test';",
        "",
        "const external = Boolean(process.env.BASE_URL);",
        f"const baseURL = process.env.BASE_URL || 'http://127.0.0.1:{ui['port']}';",
        "const channel = process.env.PW_CHANNEL || undefined; // e.g. \"chrome\" to use an installed Chrome",
        "",
        "export default defineConfig({",
        "  testDir: 'tests/e2e',",
        "  outputDir: 'reports/e2e-artifacts',",
        "  workers: 1,",
        "  reporter: [['list'], ['junit', { outputFile: 'reports/e2e-junit.xml' }]],",
        "  use: { baseURL, screenshot: 'on', trace: 'retain-on-failure', channel },",
        "  projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'], channel } }],",
        "  webServer: external ? undefined : [",
        *servers,
        "  ],",
        "});",
        "",
    ])
    prefix = "" if where == "." else f"{where}/"
    return {
        "id": f"playwright:{where}", **{k: v for k, v in need.items() if not k.startswith("_")},
        "creates": {f"{prefix}playwright.config.mjs": config},
        "package_json": {"path": f"{prefix}package.json",
                         "devDependencies": {"@playwright/test": PLAYWRIGHT_VERSION},
                         "scripts": {"test:e2e": "playwright test"}},
        "after_apply": [f"cd {where} && npm install && npx playwright install chromium"],
        "suite": {f"playwright:{where}" if where != "." else "playwright": {
            "framework": "playwright", "cwd": where, "command": "npx playwright test",
            "junit": ["reports/e2e-junit.xml"], "artifacts": ["reports/e2e-artifacts/**/*.png"],
            "env": {"PW_CHANNEL": "${PW_CHANNEL}"}, "test_paths": [f"{prefix}tests/e2e"]}},
        "notes": ["Unit tests for components: Vitest (`--reporter=junit`) is the documented option; "
                  "it is not added here."],
    }


def _pytest_item(root: Path, need: dict) -> dict:
    where = need["where"]
    prefix = "" if where == "." else f"{where}/"
    return {
        "id": f"pytest:{where}", **{k: v for k, v in need.items() if not k.startswith("_")},
        "creates": {f"{prefix}pytest.ini": "[pytest]\ntestpaths = tests\n"},
        "requirements": {"path": f"{prefix}requirements-dev.txt", "add": [PYTEST_REQUIREMENT]},
        "after_apply": [f"cd {where} && python3 -m pip install -r requirements-dev.txt"],
        "suite": {f"pytest:{where}" if where != "." else "pytest": {
            "framework": "pytest", "cwd": where,
            "command": "python3 -m pytest -q -p no:cacheprovider --junitxml=reports/pytest-junit.xml",
            "junit": ["reports/pytest-junit.xml"], "artifacts": [], "test_paths": [f"{prefix}tests"]}},
        "notes": ["pytest also runs existing unittest.TestCase tests unchanged."],
    }


def _maven_item(root: Path, need: dict) -> dict:
    where = need["where"]
    prefix = "" if where == "." else f"{where}/"
    item = {"id": f"maven-reporter:{where}", **{k: v for k, v in need.items() if not k.startswith("_")},
            "pom": {"path": f"{prefix}pom.xml", "snippet": MAVEN_REPORTER_SNIPPET}, "creates": {}, "after_apply": []}
    try:
        _insert_reporter((root / where / "pom.xml").read_text(encoding="utf-8"))
    except VerifyError as e:
        item["manual"] = str(e)
    return item


def _insert_reporter(text: str) -> str:
    """pom.xml with the Surefire reporter block added; refuses where a hand edit is safer."""
    if "maven-surefire-plugin" in text:
        raise VerifyError("pom.xml already configures maven-surefire-plugin: add the <statelessTestsetReporter> "
                          "block inside its <configuration> by hand.")
    b, e = text.find("<build>"), text.find("</build>")
    if b != -1 and "<pluginManagement>" in text[b:e]:
        raise VerifyError("pom.xml uses <pluginManagement>: add the Surefire plugin block by hand.")
    plugin = "\n".join("      " + line for line in MAVEN_REPORTER_SNIPPET.splitlines())
    if b != -1:
        close = text.rfind("</plugins>", b, e)
        if close != -1:
            line = text.rfind("\n", 0, close) + 1
            return text[:line] + plugin + "\n" + text[line:]
        return text[:e] + "  <plugins>\n" + plugin + "\n    </plugins>\n  " + text[e:]
    end = text.rfind("</project>")
    if end == -1:
        raise VerifyError("pom.xml has no </project>: add the Surefire plugin block by hand.")
    return text[:end] + "  <build>\n    <plugins>\n" + plugin + "\n    </plugins>\n  </build>\n" + text[end:]


BUILDERS = {"playwright": _playwright_item, "pytest": _pytest_item, "maven-surefire": _maven_item}


# ---------------------------------------------------------------- propose / approve / apply

def _paths(cfg: dict, key: str) -> tuple[Path, Path]:
    d = out_dir(cfg, key)
    return d / "framework-proposal.json", d / "FRAMEWORK_PROPOSAL.md"


def _digest(items: list[dict]) -> str:
    return hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()


def propose(cfg: dict, key: str) -> dict:
    root = Path(cfg["_root"])
    items = [BUILDERS[n["framework"]](root, n) for n in needs(root)]
    prop = {"story": key, "created": now_iso(), "items": items, "sha256": _digest(items),
            "approval": None, "applied": None}
    jpath, mpath = _paths(cfg, key)
    write_json(jpath, prop)
    write_text(mpath, render(prop))
    return prop


def render(prop: dict) -> str:
    lines = [f"# Framework proposal · {prop['story']}", "",
             "Nothing below has been written or installed. A named person approves it with",
             f"`verify.py frameworks {prop['story']} --approve --by \"Name\"`, then",
             f"`verify.py frameworks {prop['story']} --apply` makes exactly these changes.", ""]
    if not prop["items"]:
        lines.append("Nothing to propose: every project already has a test framework, and Maven tags are kept.")
    for it in prop["items"]:
        lines += [f"## {it['id']}", "", f"Why: {it['why']}.", ""]
        if it.get("manual"):
            lines += [f"**By hand:** {it['manual']}", "", "```xml", it["pom"]["snippet"], "```", ""]
            continue
        for path, content in it.get("creates", {}).items():
            lines += [f"Create `{path}`:", "", "```", content.rstrip(), "```", ""]
        if "package_json" in it:
            pj = it["package_json"]
            lines += [f"Edit `{pj['path']}`: devDependencies {json.dumps(pj['devDependencies'])}, "
                      f"scripts {json.dumps(pj['scripts'])}.", ""]
        if "requirements" in it:
            lines += [f"Add to `{it['requirements']['path']}`: {', '.join(it['requirements']['add'])}.", ""]
        if "pom" in it:
            lines += [f"Add to `<build><plugins>` in `{it['pom']['path']}`:", "", "```xml", it["pom"]["snippet"], "```", ""]
        if it.get("suite"):
            lines += [f"Add suite `{next(iter(it['suite']))}` to verify.config.json.", ""]
        for cmd in it.get("after_apply", []):
            lines += [f"Then install (a person or Claude, after approval): `{cmd}`", ""]
        for n in it.get("notes", []):
            lines += [f"Note: {n}", ""]
    if prop.get("approval"):
        a = prop["approval"]
        lines += ["## Approval", "", f"Approved by **{a['by']}** at {a['at']}.", ""]
    if prop.get("applied"):
        lines += ["## Applied", "", f"Applied at {prop['applied']['at']}: " + ", ".join(prop["applied"]["changed"]) + ".", ""]
    return "\n".join(lines)


def _load(cfg: dict, key: str) -> dict:
    jpath, _ = _paths(cfg, key)
    prop = read_json(jpath)
    if not prop:
        raise VerifyError(f"No framework proposal for {key}. Run `verify.py frameworks {key} --propose` first.")
    return prop


def approve(cfg: dict, key: str, by: str) -> dict:
    """A person approves the proposal as it stands. Recorded with name and time."""
    if not by.strip():
        raise VerifyError("--by must name the person approving.")
    prop = _load(cfg, key)
    if not prop["items"]:
        raise VerifyError("The proposal is empty: nothing to approve.")
    prop["approval"] = {"by": by.strip(), "at": now_iso(), "sha256": _digest(prop["items"])}
    jpath, mpath = _paths(cfg, key)
    write_json(jpath, prop)
    write_text(mpath, render(prop))
    return prop["approval"]


def apply(cfg: dict, key: str) -> dict:
    """Make the approved changes. Refuses without an approval of this exact proposal."""
    root = Path(cfg["_root"])
    prop = _load(cfg, key)
    a = prop.get("approval")
    if not a:
        raise VerifyError(f"Not approved. A person runs `verify.py frameworks {key} --approve --by \"Name\"` first.")
    if a.get("sha256") != _digest(prop["items"]):
        raise VerifyError("The proposal changed after it was approved. Propose again and get a new approval.")
    if prop.get("applied"):
        raise VerifyError(f"Already applied at {prop['applied']['at']}.")
    items = [it for it in prop["items"] if not it.get("manual")]
    clash = [p for it in items for p in it.get("creates", {}) if (root / p).exists()]
    if clash:
        raise VerifyError(f"Would overwrite existing file(s): {', '.join(clash)}. Nothing was changed.")
    poms = {it["pom"]["path"]: _insert_reporter((root / it["pom"]["path"]).read_text(encoding="utf-8"))
            for it in items if "pom" in it}  # compute all edits before writing any
    changed = []
    for it in items:
        for path, content in it.get("creates", {}).items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(content, encoding="utf-8")
            changed.append(path)
        if "package_json" in it:
            pj = it["package_json"]
            p = root / pj["path"]
            pkg = json.loads(p.read_text(encoding="utf-8"))
            for field in ("devDependencies", "scripts"):
                pkg.setdefault(field, {})
                for k, v in pj[field].items():
                    pkg[field].setdefault(k, v)
            p.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
            changed.append(pj["path"])
        if "requirements" in it:
            p = root / it["requirements"]["path"]
            text = p.read_text(encoding="utf-8") if p.is_file() else ""
            add = [r for r in it["requirements"]["add"] if r not in text.splitlines()]
            if add:
                p.write_text(text + ("" if not text or text.endswith("\n") else "\n") + "\n".join(add) + "\n", encoding="utf-8")
                changed.append(it["requirements"]["path"])
    for path, text in poms.items():
        (root / path).write_text(text, encoding="utf-8")
        changed.append(path)
    cfg_path = root / CONFIG_NAME
    if cfg_path.is_file():
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        added = False
        for it in items:
            for name, suite in it.get("suite", {}).items():
                if name not in raw.setdefault("suites", {}):
                    raw["suites"][name] = suite
                    added = True
        if added:
            cfg_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
            changed.append(CONFIG_NAME)
    prop["applied"] = {"at": now_iso(), "approved_by": a["by"], "changed": changed}
    jpath, mpath = _paths(cfg, key)
    write_json(jpath, prop)
    write_text(mpath, render(prop))
    return {"applied": changed, "approved_by": a["by"],
            "manual": [f"{it['id']}: {it['manual']}" for it in prop["items"] if it.get("manual")],
            "next": [c for it in items for c in it.get("after_apply", [])]}
