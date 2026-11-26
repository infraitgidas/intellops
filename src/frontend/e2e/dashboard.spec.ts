import { expect, test } from '@playwright/test';

/**
 * Smoke E2E sobre el build real (QS-1, QS-2, QS-3, QS-6).
 *
 * La API es el stub de `e2e/stub-api.mjs`: 3 buckets × 3 métricas y 3 corridas
 * de la sonda, con `X-API-Key` obligatoria.
 */

const VALID_KEY = 'ilp_stub_valida';
/** Única clave de `sessionStorage` (D2). */
const SESSION_KEY_STORAGE = 'intellops.api_key';

/** Falla cualquier excepción o `console.error` de la página. */
function trackConsoleErrors(page: import('@playwright/test').Page): string[] {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      errors.push(message.text());
    }
  });
  page.on('pageerror', (error) => errors.push(error.message));
  return errors;
}

async function connect(page: import('@playwright/test').Page, apiKey: string): Promise<void> {
  await page.getByLabel('API key').fill(apiKey);
  await page.getByRole('button', { name: 'Conectar' }).click();
}

test('el gate de key aparece primero y no consulta /metrics/*', async ({ page }) => {
  const metricsRequests: string[] = [];
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.startsWith('/metrics/')) {
      metricsRequests.push(request.url());
    }
  });

  await page.goto('/');

  await expect(page.getByRole('heading', { name: /panel de operación/i })).toBeVisible();
  await expect(page.getByLabel('API key')).toBeVisible();
  await expect(page.getByLabel('API key')).toHaveAttribute('type', 'password');

  // Nada de `/metrics/*` antes de que el operador pegue la key.
  await page.waitForTimeout(500);
  expect(metricsRequests).toEqual([]);
});

test('una key inválida muestra el error y vuelve al gate', async ({ page }) => {
  await page.goto('/');
  await connect(page, 'ilp_incorrecta');

  await expect(page.getByRole('alert')).toContainText('invalid_api_key');
  await expect(page.getByLabel('API key')).toBeVisible();
  expect(await page.evaluate(() => window.sessionStorage.getItem('intellops.api_key'))).toBeNull();
});

test('con una key válida la vista de latencias pinta la serie y las sondas', async ({ page }) => {
  const consoleErrors = trackConsoleErrors(page);

  await page.goto('/');
  await connect(page, VALID_KEY);

  await expect(page.getByRole('heading', { name: 'Latencias RUM' })).toBeVisible();
  await expect(page.locator('svg.series-chart polyline')).toBeVisible();

  // Un punto por bucket del stub y la tabla de sondas con sus corridas.
  await expect(page.locator('svg.series-chart circle')).toHaveCount(3);
  const probeTable = page.locator('table.probe-table');
  await expect(probeTable).toBeVisible();
  await expect(probeTable.locator('tbody tr')).toHaveCount(3);
  await expect(probeTable).toContainText('http://127.0.0.1:8000/health');
  await expect(probeTable).toContainText('http_error');

  expect(consoleErrors).toEqual([]);
});

test('el heatmap pinta la grilla y la tabla accesible con los mismos valores', async ({ page }) => {
  const consoleErrors = trackConsoleErrors(page);

  await page.goto('/');
  await connect(page, VALID_KEY);
  await expect(page.getByRole('heading', { name: 'Latencias RUM' })).toBeVisible();

  await page.getByRole('button', { name: 'Heatmap UX' }).click();

  await expect(page.getByRole('heading', { name: 'Heatmap UX' })).toBeVisible();
  // 3 métricas × 3 buckets: una celda por combinación.
  await expect(page.locator('.heatmap-cell')).toHaveCount(9);
  await expect(page.locator('.heatmap-row-name').first()).toHaveText('TTFB');
  await expect(page.locator('.heatmap-cell[data-empty="false"]').first()).toBeVisible();

  await page.getByRole('button', { name: 'Ver como tabla' }).click();

  const heatmapTable = page.locator('table.heatmap-table');
  await expect(heatmapTable).toBeVisible();
  await expect(heatmapTable).toContainText('TTFB');
  await expect(heatmapTable).toContainText('JS_EXCEPTION_RATE');
  await expect(heatmapTable).toContainText('240 · 11 sesiones');
  await expect(heatmapTable).toContainText('0.0200 · 11 sesiones');

  expect(consoleErrors).toEqual([]);
});

test('la key de la sesión sobrevive a una recarga y el panel no la muestra', async ({ page }) => {
  await page.goto('/');
  await connect(page, VALID_KEY);
  await expect(page.getByRole('heading', { name: 'Latencias RUM' })).toBeVisible();

  await page.reload();

  // Sin gate de nuevo (la key vive en esta pestaña) y sin la key en el DOM.
  await expect(page.getByRole('heading', { name: 'Latencias RUM' })).toBeVisible();
  await expect(page.getByLabel('API key')).toHaveCount(0);
  expect(await page.content()).not.toContain(VALID_KEY);
  expect(await page.evaluate((name) => window.sessionStorage.getItem(name), SESSION_KEY_STORAGE)).toBe(
    VALID_KEY,
  );
});
