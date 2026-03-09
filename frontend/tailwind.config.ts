import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ["var(--font-heading)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"]
      },
      colors: {
        brand: {
          brown: "var(--brand-brown)",
          cream: "var(--brand-cream)",
          beige: "var(--brand-beige)",
          ink: "var(--brand-ink)",
          forest: "var(--brand-forest)",
          "forest-light": "var(--brand-forest-light)",
          gold: "var(--brand-gold)",
          "gold-light": "var(--brand-gold-light)",
          terracotta: "var(--brand-terracotta)",
          indigo: "var(--brand-indigo)"
        }
      },
      boxShadow: {
        card: "0 2px 8px rgba(26, 18, 7, 0.04)",
        "card-hover": "0 8px 24px rgba(26, 18, 7, 0.1)"
      }
    }
  },
  plugins: [typography]
};

export default config;
