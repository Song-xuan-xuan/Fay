/// <reference types="vite/client" />

export {};

declare global {
  interface ImportMetaEnv {
    readonly VITE_MCP_PROXY_TARGET?: string;
  }

  const __FAY_WS_URL__: string;
}

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    requiresRole?: 'admin' | 'user';
    public?: boolean;
  }
}
