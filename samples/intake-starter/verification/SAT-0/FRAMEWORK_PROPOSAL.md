# Framework proposal · SAT-0

Nothing below has been written or installed. A named person approves it with
`verify.py frameworks SAT-0 --approve --by "Name"`, then
`verify.py frameworks SAT-0 --apply` makes exactly these changes.

## maven-reporter:backend

Why: Surefire drops JUnit 5 @DisplayName, so 'KEY AC-n' tags would be lost.

Add to `<build><plugins>` in `backend/pom.xml`:

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <statelessTestsetReporter implementation="org.apache.maven.plugin.surefire.extensions.junit5.JUnit5Xml30StatelessReporter">
      <usePhrasedTestCaseMethodName>true</usePhrasedTestCaseMethodName>
    </statelessTestsetReporter>
  </configuration>
</plugin>
```

## playwright:frontend

Why: web front end with no test framework.

Create `frontend/playwright.config.mjs`:

```
// Playwright for this front end, proposed by verify.py frameworks (INTENT-003).
// BASE_URL points the suite at a running DEV/UAT host; without it Playwright starts
// the API and the UI locally.
import { defineConfig, devices } from '@playwright/test';

const external = Boolean(process.env.BASE_URL);
const baseURL = process.env.BASE_URL || 'http://127.0.0.1:5173';
const channel = process.env.PW_CHANNEL || undefined; // e.g. "chrome" to use an installed Chrome

export default defineConfig({
  testDir: 'tests/e2e',
  outputDir: 'reports/e2e-artifacts',
  workers: 1,
  reporter: [['list'], ['junit', { outputFile: 'reports/e2e-junit.xml' }]],
  use: { baseURL, screenshot: 'on', trace: 'retain-on-failure', channel },
  projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'], channel } }],
  webServer: external ? undefined : [
    { command: 'mvn -B -q spring-boot:run', cwd: '../backend', port: 8080, timeout: 180_000, reuseExistingServer: !process.env.CI },
    { command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort', url: 'http://127.0.0.1:5173', timeout: 60_000, reuseExistingServer: !process.env.CI },
  ],
});
```

Edit `frontend/package.json`: devDependencies {"@playwright/test": "^1.65.1"}, scripts {"test:e2e": "playwright test"}.

Add suite `playwright:frontend` to verify.config.json.

Then install (a person or Claude, after approval): `cd frontend && npm install && npx playwright install chromium`

Note: Unit tests for components: Vitest (`--reporter=junit`) is the documented option; it is not added here.

## Approval

Approved by **Mark Kendall** at 2026-11-21T16:43:19Z.

## Applied

Applied at 2026-11-21T16:43:19Z: frontend/playwright.config.mjs, frontend/package.json, backend/pom.xml, verify.config.json.

## Amendment

Approved by **Mark Kendall** at 2026-11-21T16:44:54Z: `frontend/playwright.config.mjs` UI test port 5173 → 5310 (5173 was held by another local dev server; the runner sets CI=1, so Playwright won't reuse a server).
