/// <reference types="vite/client" />

// Variables de entorno del build (D6/D2): la base de la API se lee en runtime
// desde el bundle; nunca se hornea una key.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
