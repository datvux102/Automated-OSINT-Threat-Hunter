import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#09111f",
        mist: "#d8e4f2",
        steel: "#6d7e90",
        signal: "#6ee7b7",
        ember: "#f97316",
        alarm: "#ef4444",
        canvas: "#f2f5f9",
      },
      fontFamily: {
        sans: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 24px 80px rgba(11, 25, 47, 0.12)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(9, 17, 31, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(9, 17, 31, 0.04) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
} satisfies Config;
