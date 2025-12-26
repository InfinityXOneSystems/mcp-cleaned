import React from 'react'

export const COLOR_THEME = {
  // Primary colors
  electric_blue: '#0066ff',
  electric_blue_light: '#3399ff',
  electric_blue_dark: '#0052cc',
  
  // Accent
  neon_green: '#00ff41',
  neon_green_dim: '#00cc33',
  
  // Background
  glass_dark: '#0f0f0f',
  glass_darker: '#0a0a0a',
  glass_accent: '#1a1a2e',
  
  // Typography
  text_primary: '#ffffff',
  text_secondary: '#a0a0a0',
  text_muted: '#606060',
  
  // Status colors
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
}

export const ThemeContext = React.createContext(COLOR_THEME)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeContext.Provider value={COLOR_THEME}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return React.useContext(ThemeContext)
}
