#!/usr/bin/env node
/**
 * Gate de tamaño del build estático (ISS-B-05 D6 / QS-5).
 *
 * Suma los bytes raw de todos los archivos de `dist/` e informa el gzip de los
 * `.js`/`.css`. Falla con exit 1 si el total raw supera 1 000 000 B o si no hay
 * build (el gate no puede pasar sin `dist/`).
 */

import { existsSync } from 'node:fs';
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIST_DIR = path.join(PROJECT_ROOT, 'dist');
const RAW_LIMIT = 1_000_000;

function formatBytes(bytes) {
  if (bytes >= 1_000_000) {
    return `${(bytes / 1_000_000).toFixed(2)} MB`;
  }
  if (bytes >= 1_000) {
    return `${(bytes / 1_000).toFixed(1)} kB`;
  }
  return `${bytes} B`;
}

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectFiles(fullPath)));
    } else if (entry.isFile()) {
      files.push(fullPath);
    }
  }
  return files;
}

async function main() {
  if (!existsSync(DIST_DIR)) {
    console.error(
      'check-size: no existe dist/. Corré "npm run build" antes del gate de tamaño (QS-5).',
    );
    process.exit(1);
  }

  const files = await collectFiles(DIST_DIR);
  if (files.length === 0) {
    console.error('check-size: dist/ está vacío. Corré "npm run build" antes del gate (QS-5).');
    process.exit(1);
  }

  let rawTotal = 0;
  let gzipTotal = 0;
  for (const file of files) {
    const bytes = await readFile(file);
    rawTotal += bytes.length;
    if (file.endsWith('.js') || file.endsWith('.css')) {
      gzipTotal += gzipSync(bytes).length;
    }
  }

  console.log(`dist/: ${files.length} archivos, raw ${formatBytes(rawTotal)} (${rawTotal} B)`);
  console.log(`js/css gzip: ${formatBytes(gzipTotal)} (${gzipTotal} B)`);
  console.log(`presupuesto raw: ${formatBytes(RAW_LIMIT)} (${RAW_LIMIT} B)`);

  if (rawTotal > RAW_LIMIT) {
    console.error(
      `check-size: el bundle supera el presupuesto: raw ${rawTotal} B > ${RAW_LIMIT} B (QS-5).`,
    );
    process.exit(1);
  }

  console.log('check-size: OK');
}

await main();
