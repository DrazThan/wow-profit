/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        wow: {
          gold: '#ffd100',
          'gold-light': '#ffe566',
          'gold-dark': '#b8960c',
          brown: '#2a1a0a',
          'brown-light': '#3d2610',
          parchment: '#f5e6c8',
          'border': '#5a3e1b',
          gray: '#8b8b8b',
          green: '#1eff00',
          blue: '#0070dd',
          purple: '#a335ee',
          orange: '#ff8000',
          red: '#ff2020',
          white: '#ffffff',
          common: '#9d9d9d',
        },
        quality: {
          1: '#9d9d9d',
          2: '#1eff00',
          3: '#0070dd',
          4: '#a335ee',
          5: '#ff8000',
        },
      },
      fontFamily: {
        wow: ['"LifeCraft"', '"Cinzel"', 'serif'],
      },
    },
  },
  plugins: [],
}
