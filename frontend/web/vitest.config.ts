// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  test: {
    environment: 'jsdom', // React コンポーネントのテストには jsdom を利用
    globals: true, // グローバル変数を利用する
    setupFiles: ['./tests/setup.ts'], // セットアップファイルを読み込む
    include: ['tests/**/*.test.{ts,tsx}', 'tests/**/*.spec.{ts,tsx}'],
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./', import.meta.url)), // tsconfig.json のエイリアスに合わせる
    },
  },
});
