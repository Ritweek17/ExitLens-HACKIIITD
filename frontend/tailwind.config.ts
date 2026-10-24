import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#FAF9F7",
        foreground: "#191817",
        ivory: {
          50: "#FCFCFB",
          100: "#FAF9F7",
          200: "#F3F1EA",
          300: "#EAE7DD",
          400: "#DCD8CB",
        },
        charcoal: {
          900: "#141312",
          850: "#1A1918",
          800: "#242220",
          700: "#363431",
          600: "#524F4B",
          500: "#6B6762",
          400: "#8C8780",
          300: "#B3ADA4",
          200: "#D6D1C9",
          100: "#ECE8E2",
          50: "#F7F5F2",
        },
        border: "#E8E5DC",
      },
      fontFamily: {
        serif: [
          "Newsreader",
          "Lora",
          "Charter",
          "Georgia",
          "Cambria",
          "Times New Roman",
          "Times",
          "serif",
        ],
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(20, 19, 18, 0.04), 0 1px 2px -1px rgba(20, 19, 18, 0.04)",
        dropdown: "0 10px 25px -5px rgba(20, 19, 18, 0.08), 0 8px 10px -6px rgba(20, 19, 18, 0.04)",
        elevated: "0 20px 30px -10px rgba(20, 19, 18, 0.07), 0 10px 10px -5px rgba(20, 19, 18, 0.03)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
    },
  },
  plugins: [],
};

export default config;
