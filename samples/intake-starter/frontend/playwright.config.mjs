// Playwright for this front end, proposed by verify.py frameworks (INTENT-003).
// BASE_URL points the suite at a running DEV/UAT host; without it Playwright starts
// the API and the UI locally.
import { defineConfig, devices } from '@playwright/test';

const external = Boolean(process.env.BASE_URL);
const baseURL = process.env.BASE_URL || 'http://127.0.0.1:5310';
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
    { command: 'npm run dev -- --host 127.0.0.1 --port 5310 --strictPort', url: 'http://127.0.0.1:5310', timeout: 60_000, reuseExistingServer: !process.env.CI },
  ],
});
