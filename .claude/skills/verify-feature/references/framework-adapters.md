# Using the team's own frameworks

verify.py does not ship a test framework and never installs one. A suite in
`verify.config.json` is the command the team already runs, plus where its JUnit XML lands.

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
root) is where Gate 2 looks for `@ai-proposed` markers.

## Getting JUnit XML

| Framework | How |
|---|---|
| Playwright | reporter `['junit', { outputFile: 'reports/e2e-junit.xml' }]` in the config, or `PLAYWRIGHT_JUNIT_OUTPUT_NAME` with `--reporter=junit`. Screenshots appear as `[[ATTACHMENT|...]]` and are linked as evidence. |
| node:test (Node 20+) | `node --test --test-reporter=junit --test-reporter-destination=reports/api-junit.xml` (add a second `spec` reporter to stdout for readable logs) |
| Jest | `jest-junit` reporter (`--reporters=default --reporters=jest-junit`) |
| Vitest | `--reporter=junit --outputFile=reports/vitest-junit.xml` |
| Cypress | `--reporter junit --reporter-options mochaFile=reports/cypress-[hash].xml` |
| pytest | `--junitxml=reports/pytest-junit.xml` |
| Maven | Surefire writes `target/surefire-reports/TEST-*.xml` by default |
| Gradle | `build/test-results/test/*.xml` by default |
| Go | `gotestsum --junitfile reports/go-junit.xml` |
| .NET | `dotnet test --logger junit` (JunitXml.TestLogger) |

If the team's framework can't emit JUnit XML, add a reporter in *their* project with their
agreement. Don't add a parallel framework.

## Targeting an environment

`environments` in the config sets variables (usually `BASE_URL`) for a run:
`verify.py run SHOP-142 --env uat`. The team's tests must read that variable. With
`BASE_URL` empty, the demo app's Playwright config starts the app locally.
