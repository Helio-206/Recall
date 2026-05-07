import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0A0F",
        surface: "#111117",
        "surface-2": "#15151D",
        border: "#1F1F2A",
        primary: "#2F6BFF",
        warm: "#FFB457",
        violet: "#B97AFF",
        success: "#4CD67D",
        foreground: "#F5F7FA",
        muted: "#A1A8B3",
      },
      fontFamily: {
        heading: ["var(--font-sora)", "sans-serif"],
        body: ["var(--font-geist)", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      boxShadow: {
        premium: "0 24px 80px rgba(0, 0, 0, 0.36)",
        insetPanel: "inset 0 1px 0 rgba(255, 255, 255, 0.04)",
      },
      transitionTimingFunction: {
        premium: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
