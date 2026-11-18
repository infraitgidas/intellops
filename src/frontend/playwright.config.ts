import process from 'node:process';
import { defineConfig, devices } from '@playwright/test';

/**
 * Config del smoke E2E (ISS-B-05 D5 / QS-6).
 *
 * Dos `webServer`: la API stub (`e2e/stub-api.mjs`, puerto 8099) y el build
 * estático servido con `vite preview` (puerto 4173, `npm run preview:e2e`). El
 * smoke corre contra el artefacto real, no contra el dev server.
 *
 * `PLAYWRIGHT_CHROMIUM_PATH` permite usar un Chromium del sistema cuando la
 * revisión del cache de Playwright no coincide (`/usr/bin/chromium` en local).
 */

const API_BASE_URL = 'http://127.0.0.1:8099';
/** `vite preview` escucha en `localhost` (IPv6 ::1 en este host): se usa el mismo host. */
const PREVIEW_URL = 'http://localhost:4173';

const chromiumPath = process.env.PLAYWRIGHT_CHROMIUM_PATH;
const isCI = process.env.CI !== undefined;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: 0,
  reporter: 'list',
  outputDir: 'test-results',
  use: {
    baseURL: PREVIEW_URL,
    trace: 'off',
    launchOptions:
      chromiumPath !== undefined && chromiumPath.length > 0
        ? { executablePath: chromiumPath }
        : {},
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'node e2e/stub-api.mjs',
      // El stub responde 401 sin key: Playwright lo considera listo igual.
      url: `${API_BASE_URL}/metrics/list`,
      reuseExistingServer: !isCI,
      timeout: 20_000,
    },
    {
      command: 'npm run preview:e2e',
      url: PREVIEW_URL,
      reuseExistingServer: !isCI,
      timeout: 60_000,
    },
  ],
});
