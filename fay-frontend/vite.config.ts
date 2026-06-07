import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const flaskTarget = env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

  return {
    plugins: [vue()],
    server: {
      port: Number(env.VITE_PORT || 5173),
      proxy: {
        '/api': {
          target: flaskTarget,
          changeOrigin: true,
        },
        '/v1': {
          target: flaskTarget,
          changeOrigin: true,
        },
        '/audio': {
          target: flaskTarget,
          changeOrigin: true,
        },
        '/robot': {
          target: flaskTarget,
          changeOrigin: true,
        },
        '/static': {
          target: flaskTarget,
          changeOrigin: true,
        },
      },
    },
    define: {
      __FAY_WS_URL__: JSON.stringify(env.VITE_WS_URL || ''),
    },
  };
});
