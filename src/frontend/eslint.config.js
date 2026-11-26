import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import tseslint from 'typescript-eslint';

// Flat config. Sólo se habilitan las dos reglas clásicas de `react-hooks`
// (rules-of-hooks y exhaustive-deps): las reglas del React Compiler que trae
// el preset v7 marcan patrones legítimos de este paquete (por ejemplo el
// `setState` de `useApi` al iniciar una request).
export default tseslint.config(
  {
    ignores: ['dist/**', 'dist-e2e/**', 'playwright-report/**', 'test-results/**', 'node_modules/**', 'coverage/**'],
  },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [...tseslint.configs.recommended],
    plugins: { 'react-hooks': reactHooks },
    languageOptions: {
      globals: { ...globals.browser },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      // Sin `any` en el código fuente ni en los tests (ISS-B-05 D4).
      '@typescript-eslint/no-explicit-any': 'error',
      'no-console': 'error',
    },
  },
  {
    files: ['vite.config.ts', 'playwright.config.ts', 'e2e/**/*.{ts,mjs}', 'scripts/**/*.mjs', 'eslint.config.js'],
    languageOptions: { globals: { ...globals.node } },
    rules: { 'no-console': 'off' },
  },
);
