import React, { useState, useEffect } from 'react'
import { Github, GitBranch, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { agentService } from '@/services/firestore'
import type { Agent } from '@/types'
import { useTheme } from '@/lib/theme'

/**
 * Left Panel - GitHub & VS Code Sync
 * Shows repo status, CI/CD signals, and agent commits
 */
export function GitHubPanel() {
  const theme = useTheme()
  const [repos, setRepos] = useState<any[]>([
    {
      id: 'repo-1',
      name: 'infinity-x-mcp',
      owner: 'InfinityXOneSystems',
      branch: 'main',
      lastCommit: '7efe576e',
      lastCommitTime: new Date(Date.now() - 3600000),
      openIssues: 2,
      openPRs: 1,
      status: 'healthy',
    },
  ])

  return (
    <div className="glass-panel p-4 h-full overflow-y-auto">
      <div className="flex items-center gap-2 mb-6">
        <Github size={20} className="text-electric-blue-light" />
        <h2 className="text-lg font-semibold">Repository Sync</h2>
      </div>

      <div className="space-y-4">
        {repos.map(repo => (
          <div key={repo.id} className="bg-glass-accent border border-glass rounded-lg p-3">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-medium text-white">{repo.owner}/{repo.name}</p>
                <p className="text-xs text-slate-light flex items-center gap-1 mt-1">
                  <GitBranch size={12} /> {repo.branch}
                </p>
              </div>
              <div className="flex items-center gap-1">
                {repo.status === 'healthy' ? (
                  <CheckCircle size={16} className="text-neon-green" />
                ) : (
                  <AlertCircle size={16} className="text-error" />
                )}
              </div>
            </div>

            <div className="text-xs space-y-1 text-slate-light">
              <p>Latest: {repo.lastCommit.slice(0, 7)}</p>
              <p className="flex items-center gap-1">
                <Clock size={12} /> {formatTime(repo.lastCommitTime)}
              </p>
              <p className="mt-2">
                <span className="text-warning">⚠️ {repo.openIssues}</span> issues
                {' '}
                <span className="text-info">ℹ️ {repo.openPRs}</span> PRs
              </p>
            </div>

            <button className="w-full mt-3 text-xs py-1 bg-glass-accent border border-electric-blue rounded hover:bg-slate transition">
              View on GitHub
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 divider-glass">
        <h3 className="text-sm font-semibold mb-3">Agent Commits</h3>
        <div className="text-xs text-slate-light space-y-2">
          <p>• code-agent: Auto-rebase main (2h ago)</p>
          <p>• crawler-agent: Data update (1h ago)</p>
          <p>• analyst-agent: Report generation (30m ago)</p>
        </div>
      </div>
    </div>
  )
}

function formatTime(date: Date): string {
  const diff = Date.now() - date.getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return `${Math.floor(diff / 60000)}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

/**
 * Right Panel - Multi-Agent Chat & Notifications
 */
export function ChatPanel() {
  const theme = useTheme()
  const [agents, setAgents] = useState<Agent[]>([])
  const [messages, setMessages] = useState<any[]>([
    {
      id: '1',
      type: 'system',
      message: 'Vision Cortex activated. Monitoring 8 agents.',
      timestamp: new Date(),
    },
    {
      id: '2',
      type: 'agent',
      agent: 'Crawler Agent',
      message: '4 parallel crawlers running. Real estate data updated: +12 distressed properties detected.',
      timestamp: new Date(Date.now() - 300000),
    },
  ])
  const [input, setInput] = useState('')

  useEffect(() => {
    const loadAgents = async () => {
      const allAgents = await agentService.getAllAgents()
      setAgents(allAgents.slice(0, 4)) // Show top 4
    }
    loadAgents()
  }, [])

  const handleSend = () => {
    if (!input.trim()) return
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'user',
      message: input,
      timestamp: new Date(),
    }])
    setInput('')
  }

  return (
    <div className="glass-panel p-4 h-full flex flex-col">
      <h2 className="text-lg font-semibold mb-4">Vision Cortex & Agents</h2>

      {/* Agents Status */}
      <div className="mb-4 space-y-2">
        <p className="text-xs font-semibold text-slate-light">ACTIVE AGENTS</p>
        {agents.slice(0, 3).map(agent => (
          <div key={agent.id} className="bg-glass-accent border border-glass rounded p-2">
            <div className="flex justify-between items-center">
              <span className="text-xs font-medium">{agent.name}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                agent.status === 'running' ? 'bg-neon-green text-glass-darker' : 'bg-slate text-slate-light'
              }`}>
                {agent.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="divider-glass my-4"></div>

      {/* Chat */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.map(msg => (
          <div key={msg.id} className={`text-xs ${msg.type === 'user' ? 'text-right' : ''}`}>
            {msg.type === 'system' && (
              <p className="text-slate-light italic">{msg.message}</p>
            )}
            {msg.type === 'agent' && (
              <div className="text-left">
                <p className="text-neon-green font-medium text-xs mb-1">{msg.agent}</p>
                <p className="text-slate-light bg-glass-accent px-3 py-2 rounded inline-block max-w-xs">
                  {msg.message}
                </p>
              </div>
            )}
            {msg.type === 'user' && (
              <p className="text-electric-blue bg-glass-accent px-3 py-2 rounded inline-block">
                {msg.message}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask agents..."
          className="input-glass flex-1"
        />
        <button onClick={handleSend} className="btn-primary">
          →
        </button>
      </div>
    </div>
  )
}
