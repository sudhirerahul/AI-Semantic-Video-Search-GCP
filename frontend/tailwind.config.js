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
          // Control-room charcoal - dark graphite, midnight slate
          dark: '#0D0E11',
          surface: '#12131A',
          border: 'rgba(255,255,255,0.05)',
          hover: 'rgba(255,255,255,0.06)',
          text: {
            // Near-white for active/primary (sharp against dark)
            primary: '#E8E9ED',
            // Cool muted gray for inactive tabs (subdued but readable)
            secondary: '#7B7D85',
            // Dimmer for numbers/metadata
            tertiary: '#52545C',
          },
          accent: {
            // Cool indigo for active tab underline (precise, not decorative)
            primary: '#6366F1',
            hover: '#7C7FF6',
          }
        }
      },
      fontFamily: {
        // Inter with tight spacing - clean, compact, engineered
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      letterSpacing: {
        'tighter': '-0.02em',
      },
    },
  },
  plugins: [],
}
