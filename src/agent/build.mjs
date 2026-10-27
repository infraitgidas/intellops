// Build del agente RUM (ISS-B-01).
//
// Genera un único IIFE minificado en dist/rum.js y verifica el presupuesto de
// bundle del contrato A.3 §10: tope duro 30 KB gzip (30720 bytes), objetivo
// 20 KB. `--check-only` mide un dist/rum.js existente sin reconstruir.
import { build } from "esbuild";
import { gzipSync } from "node:zlib";
import { readFileSync, mkdirSync } from "node:fs";

const MAX_GZIP_BYTES = 30720;
const TARGET_GZIP_BYTES = 20480;
const OUT = "dist/rum.js";

async function bundle() {
  mkdirSync("dist", { recursive: true });
  await build({
    entryPoints: ["src/index.js"],
    outfile: OUT,
    bundle: true,
    minify: true,
    format: "iife",
    globalName: "IntellOpsRUM",
    target: ["es2020"],
    legalComments: "none",
    charset: "ascii",
  });
}

function report() {
  const raw = readFileSync(OUT);
  const gzip = gzipSync(raw, { level: 9 }).length;
  const status = gzip <= MAX_GZIP_BYTES ? "OK" : "EXCEDE";
  console.log(
    `bundle: ${OUT} — ${raw.length} bytes sin comprimir, ${gzip} bytes gzip ` +
      `(tope ${MAX_GZIP_BYTES}, objetivo ${TARGET_GZIP_BYTES}) → ${status}`,
  );
  return gzip <= MAX_GZIP_BYTES;
}

const checkOnly = process.argv.includes("--check-only");
if (!checkOnly) await bundle();
if (!report()) process.exit(1);
