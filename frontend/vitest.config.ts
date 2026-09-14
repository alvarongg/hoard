import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}", "tests/**/*.test.{ts,tsx}"],
    css: true,
    env: {
      VITE_API_URL: "http://localhost:8000/api",
    },
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/**",
        "src/test/**",
        "src/vite-env.d.ts",
        "src/main.tsx",
        "**/*.config.ts",
        "**/*.d.ts",
        "src/types/**",
        "tests/**",
        "src/tests/**",
        "**/*.spec.ts",
      ],
      thresholds: {
        lines: 80,
      },
    },
  },
});
