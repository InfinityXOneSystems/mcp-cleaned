/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Black glass morphic theme
        'glass-dark': '#0f0f0f',
        'glass-darker': '#0a0a0a',
        'glass-accent': '#1a1a2e',
        
        // Electric blue accents
        'electric-blue': '#0066ff',
        'electric-blue-light': '#3399ff',
        'electric-blue-dark': '#0052cc',
        
        // Neon green
        'neon-green': '#00ff41',
        'neon-green-dim': '#00cc33',
        
        // Secondary
        'slate': '#1e293b',
        'slate-light': '#475569',
      },
      backgroundColor: {
        'glass': 'rgba(15, 15, 15, 0.6)',
        'glass-light': 'rgba(15, 15, 15, 0.4)',
      },
      backdropBlur: {
        'xl': '12px',
        '2xl': '20px',
      },
      borderColor: {
        'glass': 'rgba(51, 153, 255, 0.2)',
        'glass-accent': 'rgba(0, 255, 65, 0.1)',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glow-blue': '0 0 20px rgba(0, 102, 255, 0.3)',
        'glow-green': '0 0 15px rgba(0, 255, 65, 0.2)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'drift': 'drift 20s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(0, 102, 255, 0.3)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 30px rgba(0, 102, 255, 0.5)' },
        },
        'drift': {
          '0%, 100%': { transform: 'translateX(0)' },
          '50%': { transform: 'translateX(20px)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
