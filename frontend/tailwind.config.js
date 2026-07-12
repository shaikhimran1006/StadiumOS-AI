/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        stadium: {
          blue: '#1a237e',
          'blue-light': '#283593',
          'blue-dark': '#0d1442',
          green: '#2e7d32',
          'green-light': '#43a047',
          'green-dark': '#1b5e20',
          gold: '#f9a825',
          'gold-light': '#fbc02d',
          'gold-dark': '#f57f17',
        },
        dark: {
          bg: '#0a0e27',
          surface: '#111638',
          card: '#1a1f4a',
          border: '#2a2f5a',
          hover: '#242860',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};
