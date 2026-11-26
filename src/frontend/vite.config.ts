import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Build estático (ADR-0010): la SPA se sirve aparte del compose y nunca
// necesita la API en tiempo de build. `VITE_API_BASE_URL` sólo se lee en
// runtime desde el bundle.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    restoreMocks: true,
  },
});
