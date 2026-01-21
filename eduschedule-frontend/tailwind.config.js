// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#005F73',   // Deep Teal
        'brand-secondary': '#0A9396', // Lighter Teal
        'brand-accent': '#EE9B00',    // Gold Accent
        'brand-dark': '#232323',      // Almost Black
        'brand-light': '#F8F9FA',     // Off-White
        'brand-gray': '#6C757D',      // Muted Gray
      },
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
