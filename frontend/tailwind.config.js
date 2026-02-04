/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0B0F14',
          surface: '#0E1216',
          border: 'rgba(255,255,255,0.06)',
          hover: 'rgba(255,255,255,0.08)',
          text: {
            primary: '#ECECF1',
            secondary: '#9B9CA3',
            tertiary: '#6E6F73',
          },
          accent: {
            primary: '#7C3AED',
            hover: '#8B5CF6',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
