import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0d0f12",
        foreground: "#f3f4f6",
        surface: {
          50: "#181a20",
          100: "#1e2128",
          200: "#272a34",
          300: "#323742",
        },
        primary: {
          DEFAULT: "#6366f1",
          hover: "#4f46e5",
          muted: "rgba(99, 102, 241, 0.15)",
        },
        accent: {
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
      },
    },
  },
  plugins: [],
};
export default config;
