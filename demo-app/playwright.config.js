// Playwright config for the demo shop.
// BASE_URL points the suite at a running DEV/UAT environment; without it,
// Playwright builds and starts the app locally.
import { defineConfig, devices } from '@playwright/test';

const external = Boolean(process.env.BASE_URL);
const baseURL = process.env.BASE_URL || 'http://127.0.0.1:4310';
const channel = process.env.PW_CHANNEL || undefined; // e.g. "chrome" to use an installed Chrome

export default defineConfig({
  testDir: 'tests/e2e',
  outputDir: 'reports/e2e-artifacts',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [
    ['list'],
    ['junit', { outputFile: 'reports/e2e-junit.xml' }],
    ['html', { open: 'never', outputFolder: 'reports/e2e-html' }],
  ],
  use: { baseURL, screenshot: 'on', trace: 'retain-on-failure', channel },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], channel } },
    { name: 'mobile', use: { ...devices['Pixel 7'], channel } },
  ],
  webServer: external
    ? undefined
    : { command: 'npm run build && npm start', url: `${baseURL}/api/health`, reuseExistingServer: true, timeout: 120000 },
});
