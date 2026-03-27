import { resolve } from 'node:path';
import { defineConfig } from 'vite';

const requestedPort = Number(process.env.TAURI_DEV_PORT || process.env.PORT || 5173);
const hasFixedPort = Boolean(process.env.TAURI_DEV_PORT || process.env.PORT);

export default defineConfig({
  clearScreen: false,
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.js'],
    include: ['src/__tests__/**/*.test.js'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.js'],
      exclude: ['src/__tests__/**', 'src/bubble.js'],
    },
    server: {
      deps: {
        inline: ['@tauri-apps/plugin-shell', '@tauri-apps/api'],
      },
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        bubble: resolve(__dirname, 'bubble.html'),
        settings: resolve(__dirname, 'settings.html'),
        chat: resolve(__dirname, 'chat.html'),
        'context-menu': resolve(__dirname, 'context-menu.html'),
      },
    },
  },
  server: {
    port: requestedPort,
    strictPort: hasFixedPort,
  },
  envPrefix: ['VITE_', 'TAURI_'],
});
