import { generateTailwindTheme } from './src/theme/tailwind-theme.js';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: generateTailwindTheme(),
  },
  plugins: [],
}
