/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        teal: {
          50:  '#EAF3EF',
          100: '#D5E7DF',
          200: '#AACFC0',
          300: '#80B7A0',
          400: '#559F80',
          500: '#427A76',
          600: '#366462',
          700: '#254B45',
          800: '#1A3530',
          900: '#0F1F1C',
        },
        brand: {
          primary:    '#427A76',
          dark:       '#254B45',
          mint:       '#EAF3EF',
          background: '#F6F8F7',
          text:       '#203331',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 12px 0 rgba(0,0,0,0.10)',
      },
    },
  },
  plugins: [],
}
