import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const backendTarget = env.VITE_BACKEND_PROXY_TARGET || 'http://localhost:8000';

  const proxyRoutes = [
    '/parse',
    '/queries',
    '/run',
    '/filters',
    '/announcements',
    '/smart-suggestions',
    '/company-suggestions',
    '/report-suggestions',
    '/parse-build-run',
    '/health',
  ];

  const proxy = proxyRoutes.reduce((acc, route) => {
    acc[route] = {
      target: backendTarget,
      changeOrigin: true,
      secure: false,
    };
    return acc;
  }, {} as Record<string, { target: string; changeOrigin: boolean; secure: boolean }>);

  return {
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy,
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
  };
});
