/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_AI_SERVICE_URL: string
  readonly VITE_DIRECT_AI_MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

