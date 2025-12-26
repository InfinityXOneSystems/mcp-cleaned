import type { Agent } from '@/types'

/**
 * Agent Registry - Pre-configured agent templates
 * These are the 8 core agents that power the Infinity X system
 */

export const AGENT_REGISTRY: Record<string, Agent> = {
  // Validator Agent - Governance and correctness enforcement
  validator: {
    id: 'validator-1',
    name: 'Validator Agent',
    type: 'validator',
    description: 'Governance enforcement and correctness validation across all operations',
    enabled: true,
    status: 'idle',
    interval: 60, // Check every minute
    version: '1.0.0',
    config: {
      rules: ['no-secrets-in-logs', 'no-unsafe-operations', 'demo-mode-enforcement'],
      dryRunDefault: true,
      auditLog: true,
    },
  },

  // Crawler Agent - Parallel headless scraping
  crawler: {
    id: 'crawler-1',
    name: 'Crawler Agent',
    type: 'crawler',
    description: 'Parallel headless browser automation for market intelligence gathering',
    enabled: true,
    status: 'idle',
    interval: 300, // Every 5 minutes
    version: '1.0.0',
    config: {
      maxParallel: 4,
      timeout: 30000,
      retries: 3,
      headless: true,
      industries: ['real-estate', 'finance', 'tech', 'e-commerce'],
    },
  },

  // Scraper Agent - DOM manipulation and form interaction
  scraper: {
    id: 'scraper-1',
    name: 'Scraper Agent',
    type: 'scraper',
    description: 'Advanced DOM scraping, form filling, and interactive element handling',
    enabled: true,
    status: 'idle',
    interval: 600, // Every 10 minutes
    version: '1.0.0',
    config: {
      jsExecution: true,
      mouseControl: true,
      formFill: true,
      captchaDetection: true,
      delayMs: 500,
    },
  },

  // Code Agent - GitHub and VS Code operations
  code: {
    id: 'code-1',
    name: 'Code Agent',
    type: 'code',
    description: 'GitHub repository management, CI/CD visibility, and VS Code automation',
    enabled: true,
    status: 'idle',
    interval: 120, // Every 2 minutes
    version: '1.0.0',
    config: {
      gitSync: true,
      cicdMonitor: true,
      autoCommit: true,
      branchScan: true,
      codeReview: false,
    },
  },

  // Data Analyst Agent - Financial and market analysis
  analyst: {
    id: 'analyst-1',
    name: 'Data Analyst Agent',
    type: 'analyst',
    description: 'Financial analysis, market trends, distressed asset detection',
    enabled: true,
    status: 'idle',
    interval: 180, // Every 3 minutes
    version: '1.0.0',
    config: {
      analysisTypes: ['real-estate', 'lending', 'market-sentiment'],
      datawindow: 90, // days
      confidenceThreshold: 0.7,
      alertOn: ['anomalies', 'opportunities', 'risk-changes'],
    },
  },

  // Prediction Agent - ML-based forecasting
  prediction: {
    id: 'prediction-1',
    name: 'Prediction Agent',
    type: 'prediction',
    description: 'Price forecasts, demand signals, market movements using ML',
    enabled: true,
    status: 'idle',
    interval: 3600, // Every hour
    version: '1.0.0',
    config: {
      models: ['lstm', 'xgboost', 'ensemble'],
      horizons: ['short-term', 'medium-term', 'long-term'],
      updateFrequency: 'hourly',
      confidenceScoring: true,
    },
  },

  // Sentiment Agent - Social and market sentiment analysis
  sentiment: {
    id: 'sentiment-1',
    name: 'Sentiment Agent',
    type: 'sentiment',
    description: 'Social media, news, and market sentiment analysis',
    enabled: true,
    status: 'idle',
    interval: 1800, // Every 30 minutes
    version: '1.0.0',
    config: {
      sources: ['twitter', 'reddit', 'news', 'forums'],
      keywords: ['real-estate', 'financing', 'credit', 'business'],
      sentimentModel: 'transformer-based',
      volumeTracking: true,
    },
  },

  // Vision Cortex - Proactive business intelligence partner
  'vision-cortex': {
    id: 'vision-cortex-1',
    name: 'Vision Cortex',
    type: 'vision-cortex',
    description: 'Proactive business partner - surfaces opportunities, recommends actions, proposes system builds',
    enabled: true,
    status: 'idle',
    interval: 600, // Every 10 minutes
    version: '1.0.0',
    config: {
      proactiveMode: true,
      recommendationEngine: true,
      opportunityScoring: true,
      userMessaging: true,
      systemSuggestions: true,
      buyHoldSellIndicators: true,
    },
  },
}

/**
 * Get agent by ID
 */
export function getAgent(agentId: string): Agent | undefined {
  return Object.values(AGENT_REGISTRY).find(a => a.id === agentId)
}

/**
 * Get agents by type
 */
export function getAgentsByType(type: string): Agent[] {
  return Object.values(AGENT_REGISTRY).filter(a => a.type === type)
}

/**
 * Get all agent IDs
 */
export function getAllAgentIds(): string[] {
  return Object.keys(AGENT_REGISTRY)
}

/**
 * Get all enabled agents
 */
export function getEnabledAgents(): Agent[] {
  return Object.values(AGENT_REGISTRY).filter(a => a.enabled)
}

/**
 * Calculate next run time
 */
export function calculateNextRun(agent: Agent): Date {
  if (!agent.interval) return new Date()
  const lastRun = agent.lastRun || new Date()
  return new Date(lastRun.getTime() + agent.interval * 1000)
}
