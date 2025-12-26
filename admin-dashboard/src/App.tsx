import React, { useState, useEffect } from 'react'
import { GitHubPanel, ChatPanel } from '@/components/panels/SidePanels'
import { CenterPanel } from '@/components/panels/CenterPanel'
import { ThemeProvider } from '@/lib/theme'
import '@/styles/globals.css'

/**
 * Main Dashboard Layout
 * 3-panel responsive layout:
 * - Left: GitHub/VS Code Sync
 * - Center: Intelligence Hub (Real Estate, Lending, Sentiment, Predictions)
 * - Right: Chat Panel + Agent Status
 */
function App() {
  const [dryRunMode, setDryRunMode] = useState(true)
  const [systemHealth, setSystemHealth] = useState('operational')

  return (
    <ThemeProvider>
      <div className="w-screen h-screen bg-glass-darker text-white overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-glass-accent border-b border-glass flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-electric-blue to-neon-green flex items-center justify-center">
              <span className="font-bold text-glass-darker">IX</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-glow">INFINITY X CONTROL PLANE</h1>
              <p className="text-xs text-slate-light">Enterprise Intelligence Cockpit</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* System Health Indicator */}
            <div className="flex items-center gap-2 px-3 py-1 bg-glass-accent rounded-lg border border-glass">
              <div className={`w-2 h-2 rounded-full ${
                systemHealth === 'operational' ? 'bg-neon-green animate-pulse' : 'bg-error'
              }`}></div>
              <span className="text-xs font-medium capitalize">{systemHealth}</span>
            </div>

            {/* Dry Run Toggle */}
            <button
              onClick={() => setDryRunMode(!dryRunMode)}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                dryRunMode
                  ? 'bg-warning text-black border-warning'
                  : 'bg-error text-white border-error'
              }`}
            >
              {dryRunMode ? '🟡 DRY RUN' : '🔴 LIVE'}
            </button>

            {/* User Menu */}
            <div className="flex items-center gap-2 px-3 py-1 bg-glass rounded-lg border border-glass">
              <div className="w-6 h-6 rounded-full bg-electric-blue flex items-center justify-center text-xs font-bold">
                JD
              </div>
              <span className="text-xs">Admin</span>
            </div>
          </div>
        </header>

        {/* Main Content - 3 Column Layout */}
        <div className="flex h-[calc(100vh-64px)] gap-4 p-4 bg-glass-darker overflow-hidden">
          {/* Left Panel - 20% */}
          <div className="w-1/5 hidden lg:block">
            <GitHubPanel />
          </div>

          {/* Center Panel - 60% */}
          <div className="flex-1 lg:w-3/5">
            <CenterPanel />
          </div>

          {/* Right Panel - 20% */}
          <div className="w-1/5 hidden lg:block">
            <ChatPanel />
          </div>
        </div>

        {/* Mobile Responsiveness Overlay */}
        <div className="lg:hidden fixed inset-0 bg-glass-darker flex items-center justify-center p-4">
          <div className="text-center">
            <p className="text-lg font-semibold mb-2">Dashboard optimized for desktop</p>
            <p className="text-slate-light text-sm">Resize your browser to see the full 3-panel layout</p>
          </div>
        </div>
      </div>
    </ThemeProvider>
  )
}

export default App
