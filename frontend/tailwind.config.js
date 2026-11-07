/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dodo: {
          50: "#f0f4ff",
          100: "#dbe4fe",
          200: "#bfd0fd",
          300: "#93b1fb",
          400: "#608bf7",
          500: "#3b6cf2",
          600: "#2551e5",
          700: "#1d3ec7",
          800: "#1e35a1",
          900: "#1e317f",
          950: "#0c1333",
        },
      },
    },
  },
  plugins: [],
};

