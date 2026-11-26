import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cada test arranca con el DOM limpio, sin stubs globales y sin key guardada
// (D5: `fetch` se stubbea con `vi.stubGlobal` por test, sin MSW).
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});
