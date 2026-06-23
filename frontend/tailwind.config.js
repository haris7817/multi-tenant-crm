/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "Segoe UI",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      colors: {
        // Brand — Primary Blue
        brand: {
          50: "#eff6ff",
          100: "#dbeafe", // Primary Light
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb", // Primary
          700: "#1d4ed8", // Primary Hover
          800: "#1e40af",
          900: "#1e3a8a",
        },
        // AI Purple
        ai: {
          100: "#ddd6fe", // AI Light
          500: "#8b5cf6",
          600: "#7c3aed", // AI Purple
          700: "#6d28d9",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)",
        "card-hover":
          "0 4px 12px -2px rgb(15 23 42 / 0.10), 0 2px 6px -2px rgb(15 23 42 / 0.06)",
        pop: "0 10px 30px -10px rgb(15 23 42 / 0.25)",
      },
      borderRadius: {
        xl: "0.75rem", // 12px cards
      },
    },
  },
  plugins: [],
};
