import type { Config } from "tailwindcss";
import forms from "@tailwindcss/forms";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Semantic tokens for light/dark mode
        surface: {
          DEFAULT: "var(--color-surface)",
          muted: "var(--color-surface-muted)",
        },
        content: {
          DEFAULT: "var(--color-content)",
          muted: "var(--color-content-muted)",
        },
        border: "var(--color-border)",
        accent: {
          DEFAULT: "var(--color-accent)",
          hover: "var(--color-accent-hover)",
        },
        danger: {
          DEFAULT: "var(--color-danger)",
          hover: "var(--color-danger-hover)",
        },
        success: "var(--color-success)",
        warning: "var(--color-warning)",
      },
    },
  },
  plugins: [forms],
};

export default config;
