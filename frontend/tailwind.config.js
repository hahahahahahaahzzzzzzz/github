/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0a0c14",
          panel: "rgba(16, 20, 35, 0.65)",
          panelLight: "rgba(25, 30, 50, 0.8)",
          border: "rgba(0, 243, 255, 0.15)",
          borderGlow: "rgba(0, 243, 255, 0.4)",
          red: "#ff2a5f",
          green: "#00f3ff",
          cyan: "#00f3ff",
          yellow: "#ffbe3b",
          blue: "#3b82f6",
          purple: "#9d4edd",
          gray: "#94a3b8"
        }
      },
      boxShadow: {
        cyber: "0 0 15px rgba(0, 243, 255, 0.15)",
        cyberGlow: "0 0 25px rgba(0, 243, 255, 0.35)",
        cyberRed: "0 0 20px rgba(255, 42, 95, 0.3)"
      },
      fontFamily: {
        mono: ["Consolas", "Courier New", "monospace"]
      }
    },
  },
  plugins: [],
};
