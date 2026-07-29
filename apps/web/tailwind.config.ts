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
        background: "#090A0D",
        surface: "#111318",
        "surface-2": "#16181E",
        border: "#262932",
        primary: "#4F7CFF",
        warm: "#F0A63A",
        violet: "#7C83FF",
        success: "#4FCB83",
        foreground: "#F5F7FA",
        muted: "#9AA1AD",
      },
      fontFamily: {
        heading: ["var(--font-sora)", "sans-serif"],
        body: ["var(--font-geist)", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      boxShadow: {
        premium: "0 20px 64px rgba(0, 0, 0, 0.34)",
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
