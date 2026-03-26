import { resolve } from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
  clearScreen: false,
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        bubble: resolve(__dirname, 'bubble.html'),
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  envPrefix: ['VITE_', 'TAURI_'],
});
