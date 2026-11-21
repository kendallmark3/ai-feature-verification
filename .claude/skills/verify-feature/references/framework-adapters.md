# Using the team's own frameworks

verify.py does not ship a test framework and never installs one. A suite in
`verify.config.json` is the command the team already runs, plus where its JUnit XML lands.
`init` finds projects in subfolders too (`backend/pom.xml`, `frontend/package.json`) and
proposes one suite per project with that folder as `cwd`.

```json
"e2e": {
  "framework": "playwright",
  "cwd": "demo-app",
  "command": "npx playwright test",
  "junit": ["reports/e2e-junit.xml"],
  "artifacts": ["reports/e2e-artifacts/**/*.png"],
  "env": { "PW_CHANNEL": "${PW_CHANNEL}" },
  "test_paths": ["demo-app/tests/e2e"]
}
```

`junit` and `artifacts` are globs relative to `cwd`. Old reports matching `junit` are
deleted before each run so stale results can't count. `test_paths` (relative to the repo
root) is where Gate 2 looks for `@ai-proposed` markers, which files pipeline mode withholds,
and which reviewed tests are checked for uncommitted edits.

Optional per suite: `"writes_shared_data": true` for suites that create or delete shared
data (blocked unless the environment sets `"allow_shared_data_writes": true`).

For findings, `framework` also picks a focused re-run command: `playwright`, `node-test` (when
the command is `npm run <script>`) and `pytest` are known. Others get the suite command and
the test name.

## Getting JUnit XML

| Framework | How |
|---|---|
| Playwright | reporter `['junit', { outputFile: 'reports/e2e-junit.xml' }]` in the config, or `PLAYWRIGHT_JUNIT_OUTPUT_NAME` with `--reporter=junit`. Screenshots appear as `[[ATTACHMENT|...]]` and are linked as evidence. |
| node:test (Node 20+) | `node --test --test-reporter=junit --test-reporter-destination=reports/api-junit.xml` (add a second `spec` reporter to stdout for readable logs) |
| Jest | `jest-junit` reporter: add `jest-junit` as a dev dependency (with the team's agreement), run `jest --ci --reporters=default --reporters=jest-junit`, and set `JEST_JUNIT_OUTPUT_FILE=reports/jest-junit.xml` in the suite's `env` |
| Mocha | `mocha --reporter mocha-junit-reporter --reporter-options mochaFile=reports/mocha-junit.xml` (`mocha-junit-reporter` dev dependency) |
| Vitest | `--reporter=junit --outputFile=reports/vitest-junit.xml` |
| Cypress | `--reporter junit --reporter-options mochaFile=reports/cypress-[hash].xml` |
| pytest | `--junitxml=reports/pytest-junit.xml` |
| Python `unittest` | run it through pytest, which collects `unittest.TestCase` classes unchanged: `python3 -m pytest --junitxml=reports/pytest-junit.xml`. pytest is the runner only; the tests stay `unittest`. |
| Maven | Surefire writes `target/surefire-reports/TEST-*.xml` by default. For JUnit 5 `@DisplayName` tags, add the `usePhrasedTestCaseMethodName` reporter (see `ac-tagging.md`) |
| Gradle | `build/test-results/test/*.xml` by default |
| Go | `gotestsum --junitfile reports/go-junit.xml` |
| .NET | `dotnet test --logger junit` (JunitXml.TestLogger) |

If the team's framework can't emit JUnit XML, add a reporter in *their* project with their
agreement. Don't add a parallel framework.

## When a project has no test framework

Use the team's framework whenever there is one; never add a second one or replace one. Only
when a project has none is a default proposed, and only these:

| Project | Default | What the proposal adds |
|---|---|---|
| Web front end (React, Vue, Vite, ...) | Playwright | `playwright.config.mjs` with a JUnit reporter and a `webServer` that starts the UI and, when a Spring Boot `pom.xml` is in the repo, the API too; `@playwright/test` dev dependency; a `playwright:<folder>` suite |
| Python | pytest | `pytest.ini`, `pytest` in `requirements-dev.txt`, a `pytest:<folder>` suite |
| Maven + JUnit 5 | (keeps JUnit) | the Surefire reporter block that keeps `@DisplayName` tags |

Vitest is the documented option for React component tests (`--reporter=junit`); it is not
proposed automatically.

```bash
python3 $V init                                   # notes what is missing; writes no build file
python3 $V frameworks SAT-1 --propose             # verification/SAT-1/FRAMEWORK_PROPOSAL.md
python3 $V frameworks SAT-1 --approve --by "Name" # a person, after reading the proposal
python3 $V frameworks SAT-1 --apply               # exactly the approved changes; installs nothing
cd frontend && npm install && npx playwright install chromium
```

The approval (name, time and a hash of the proposal) is kept in
`verification/<KEY>/framework-proposal.json`. If the proposal changes after approval, `--apply`
refuses. `--apply` never overwrites an existing file. Claude never runs `--approve`.

## Targeting an environment

`environments` in the config sets variables (usually `BASE_URL`) for a run:
`verify.py run SHOP-142 --env uat`. The team's tests must read that variable. With
`BASE_URL` empty, the demo app's Playwright config starts the app locally.
