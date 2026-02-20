import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          brown: "var(--brand-brown)",
          cream: "var(--brand-cream)",
          beige: "var(--brand-beige)",
          ink: "var(--brand-ink)",
          forest: "var(--brand-forest)",
          gold: "var(--brand-gold)"
        }
      },
      boxShadow: {
        card: "0 12px 30px rgba(46, 32, 15, 0.15)"
      }
    }
  },
  plugins: []
};

export default config;
