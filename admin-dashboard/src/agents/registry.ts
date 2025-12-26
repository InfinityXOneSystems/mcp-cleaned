import { Timestamp } from 'firebase/firestore'
import type { Agent, AgentTask } from '@/types'

/**
 * Enhanced Agent Registry System
 * Manages all autonomous agents with real-time tracking and metrics
 */

export interface AgentMetrics {
  totalRuns: number
  successfulRuns: number
  failedRuns: number
  averageDuration: number
  lastError?: string
  errorRate: number
  successRate: number
  uptime: number // percentage
}

export interface AgentConfig {
  apiKey?: string
  endpoint: string
  headers?: Record<string, string>
  retryAttempts: number
  timeoutMs: number
  batchSize?: number
  rateLimit?: number
  [key: string]: any
}

/**
 * Pre-configured Agent Templates
 */
export const AGENT_TEMPLATES = {
  // Property Data Scraper
  PROPERTY_SCRAPER: {
    id: 'property-scraper-1',
    name: 'Property Data Scraper',
    type: 'scraper' as const,
    description: 'Scrapes property data from county records and MLS databases',
    enabled: true,
    status: 'idle' as const,
    interval: 21600, // Every 6 hours
    version: '1.0.0',
    config: {
      endpoint: 'https://api.propertyrecords.com/v1',
      retryAttempts: 3,
      timeoutMs: 30000,
      batchSize: 100,
      rateLimit: 60,
      maxParallel: 4,
    },
  },

  // Mortgage Activity Monitor
  MORTGAGE_MONITOR: {
    id: 'mortgage-monitor-1',
    name: 'Mortgage Activity Monitor',
    type: 'crawler' as const,
    description: 'Detects mortgage filing activity and loan signals in real-time',
    enabled: true,
    status: 'idle' as const,
    interval: 3600, // Every hour
    version: '1.0.0',
    config: {
      endpoint: 'https://api.mortgagedata.com/v1',
      retryAttempts: 5,
      timeoutMs: 60000,
      batchSize: 50,
      rateLimit: 30,
      headless: true,
      jsExecution: true,
    },
  },

  // Market Sentiment Analyzer
  SENTIMENT_ANALYZER: {
    id: 'sentiment-analyzer-1',
    name: 'Market Sentiment Analyzer',
    type: 'analyst' as const,
    description: 'Analyzes market sentiment from news, social media, and trends',
    enabled: true,
    status: 'idle' as const,
    interval: 14400, // Every 4 hours
    version: '1.0.0',
    config: {
      endpoint: 'https://api.sentimentanalysis.com/v1',
      retryAttempts: 3,
      timeoutMs: 45000,
      batchSize: 200,
      rateLimit: 120,
      sources: ['twitter', 'reddit', 'news', 'forums'],
      sentimentModel: 'transformer-based',
    },
  },

  // Property Value Predictor
  VALUE_PREDICTOR: {
    id: 'value-predictor-1',
    name: 'Property Value Predictor',
    type: 'prediction' as const,
    description: 'Predicts property values using advanced ML models',
    enabled: true,
    status: 'idle' as const,
    interval: 86400, // Daily
    version: '1.0.0',
    config: {
      endpoint: 'http://localhost:8000/api/predict',
      retryAttempts: 3,
      timeoutMs: 120000,
      batchSize: 10,
      rateLimit: 20,
      models: ['lstm', 'xgboost', 'ensemble'],
      confidenceThreshold: 0.75,
    },
  },

  // Risk Assessment Engine
  RISK_ASSESSOR: {
    id: 'risk-assessor-1',
    name: 'Risk Assessment Engine',
    type: 'analyst' as const,
    description: 'Calculates comprehensive risk scores for properties and loans',
    enabled: true,
    status: 'idle' as const,
    interval: 43200, // Every 12 hours
    version: '1.0.0',
    config: {
      endpoint: 'http://localhost:8001/api/assess-risk',
      retryAttempts: 2,
      timeoutMs: 30000,
      batchSize: 50,
      rateLimit: 100,
      riskFactors: ['location', 'age', 'condition', 'market', 'legal'],
    },
  },

  // Notification Service
  NOTIFICATION_SERVICE: {
    id: 'notification-service-1',
    name: 'Notification Service',
    type: 'validator' as const,
    description: 'Sends alerts and notifications to users and systems',
    enabled: true,
    status: 'idle' as const,
    interval: 60, // Every minute
    version: '1.0.0',
    config: {
      endpoint: 'https://api.notifications.com/v1',
      retryAttempts: 5,
      timeoutMs: 10000,
      batchSize: 100,
      rateLimit: 500,
      channels: ['email', 'sms', 'push', 'webhook'],
    },
  },

  // Data Quality Monitor
  DATA_QUALITY: {
    id: 'data-quality-1',
    name: 'Data Quality Monitor',
    type: 'validator' as const,
    description: 'Monitors data integrity and quality across systems',
    enabled: true,
    status: 'idle' as const,
    interval: 10800, // Every 3 hours
    version: '1.0.0',
    config: {
      endpoint: 'http://localhost:8002/api/quality-check',
      retryAttempts: 2,
      timeoutMs: 60000,
      batchSize: 1000,
      rateLimit: 10,
      checkTypes: ['completeness', 'accuracy', 'consistency', 'timeliness'],
    },
  },

  // Vision Cortex - Proactive Intelligence
  VISION_CORTEX: {
    id: 'vision-cortex-1',
    name: 'Vision Cortex',
    type: 'analyst' as const,
    description: 'Proactive business intelligence - surfaces opportunities and recommends actions',
    enabled: true,
    status: 'idle' as const,
    interval: 600, // Every 10 minutes
    version: '1.0.0',
    config: {
      endpoint: 'http://localhost:8003/api/cortex',
      retryAttempts: 3,
      timeoutMs: 45000,
      batchSize: 1,
      proactiveMode: true,
      opportunityScoring: true,
      buyHoldSellIndicators: true,
      systemSuggestions: true,
    },
  },
}

/**
 * Agent Registry - Centralized management
 */
export class AgentRegistry {
  private agents: Map<string, Agent> = new Map()
  private tasks: Map<string, AgentTask> = new Map()

  constructor() {
    // Initialize with templates
    Object.values(AGENT_TEMPLATES).forEach((template) => {
      this.agents.set(template.id, {
        ...template,
        metrics: {
          totalRuns: 0,
          successfulRuns: 0,
          failedRuns: 0,
          averageDuration: 0,
          errorRate: 0,
          successRate: 100,
          uptime: 100,
        },
        lastRun: undefined,
        nextRun: undefined,
        createdAt: Timestamp.now(),
        updatedAt: Timestamp.now(),
      })
    })
  }

  /**
   * Register new agent from template
   */
  registerFromTemplate(templateKey: keyof typeof AGENT_TEMPLATES): string {
    const template = AGENT_TEMPLATES[templateKey]
    const id = template.id
    this.agents.set(id, {
      ...template,
      metrics: {
        totalRuns: 0,
        successfulRuns: 0,
        failedRuns: 0,
        averageDuration: 0,
        errorRate: 0,
        successRate: 100,
        uptime: 100,
      },
      createdAt: Timestamp.now(),
      updatedAt: Timestamp.now(),
    })
    return id
  }

  /**
   * Get agent by ID
   */
  getAgent(id: string): Agent | null {
    return this.agents.get(id) || null
  }

  /**
   * Get all agents
   */
  getAllAgents(): Agent[] {
    return Array.from(this.agents.values())
  }

  /**
   * Get agents by type
   */
  getAgentsByType(type: string): Agent[] {
    return Array.from(this.agents.values()).filter((a) => a.type === type)
  }

  /**
   * Get active agents
   */
  getActiveAgents(): Agent[] {
    return Array.from(this.agents.values()).filter((a) => a.status === 'running')
  }

  /**
   * Update agent status
   */
  updateAgentStatus(id: string, status: Agent['status']): void {
    const agent = this.agents.get(id)
    if (agent) {
      agent.status = status
      agent.updatedAt = Timestamp.now()
    }
  }

  /**
   * Update agent metrics
   */
  updateMetrics(id: string, metrics: Partial<AgentMetrics>): void {
    const agent = this.agents.get(id)
    if (agent) {
      agent.metrics = { ...agent.metrics, ...metrics }
      agent.updatedAt = Timestamp.now()
    }
  }

  /**
   * Record agent run
   */
  recordRun(
    id: string,
    success: boolean,
    duration: number,
    error?: string
  ): void {
    const agent = this.agents.get(id)
    if (agent) {
      const metrics = agent.metrics
      metrics.totalRuns++
      if (success) {
        metrics.successfulRuns++
      } else {
        metrics.failedRuns++
        if (error) metrics.lastError = error
      }
      metrics.errorRate = (metrics.failedRuns / metrics.totalRuns) * 100
      metrics.successRate = (metrics.successfulRuns / metrics.totalRuns) * 100
      metrics.averageDuration =
        (metrics.averageDuration * (metrics.totalRuns - 1) + duration) /
        metrics.totalRuns

      agent.lastRun = Timestamp.now()
      agent.nextRun = new Timestamp(
        Math.floor((Date.now() + agent.interval * 1000) / 1000),
        0
      )
      agent.updatedAt = Timestamp.now()
    }
  }

  /**
   * Create and queue task
   */
  createTask(agentId: string, input: Record<string, any>, priority = 0): string {
    const agent = this.agents.get(agentId)
    if (!agent) throw new Error(`Agent ${agentId} not found`)

    const taskId = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const task: AgentTask = {
      id: taskId,
      agentId,
      status: 'pending',
      input,
      priority,
      retryCount: 0,
      createdAt: Timestamp.now(),
    }
    this.tasks.set(taskId, task)
    return taskId
  }

  /**
   * Get task
   */
  getTask(id: string): AgentTask | null {
    return this.tasks.get(id) || null
  }

  /**
   * Get agent tasks
   */
  getAgentTasks(agentId: string): AgentTask[] {
    return Array.from(this.tasks.values()).filter((t) => t.agentId === agentId)
  }

  /**
   * Get pending tasks
   */
  getPendingTasks(): AgentTask[] {
    return Array.from(this.tasks.values()).filter((t) => t.status === 'pending')
  }

  /**
   * Update task status
   */
  updateTaskStatus(
    id: string,
    status: AgentTask['status'],
    output?: Record<string, any>,
    error?: string
  ): void {
    const task = this.tasks.get(id)
    if (task) {
      task.status = status
      task.endTime = Timestamp.now()
      if (task.startTime) {
        task.duration =
          task.endTime.toMillis() - (task.startTime as any).toMillis?.()
      }
      if (output) task.output = output
      if (error) task.error = error
    }
  }

  /**
   * Get registry statistics
   */
  getStats(): {
    totalAgents: number
    activeAgents: number
    totalTasks: number
    pendingTasks: number
    completedTasks: number
    failedTasks: number
    averageSuccessRate: number
    averageErrorRate: number
  } {
    const allAgents = Array.from(this.agents.values())
    const allTasks = Array.from(this.tasks.values())

    const avgSuccessRate =
      allAgents.length > 0
        ? allAgents.reduce((sum, a) => sum + a.metrics.successRate, 0) /
          allAgents.length
        : 0

    const avgErrorRate =
      allAgents.length > 0
        ? allAgents.reduce((sum, a) => sum + a.metrics.errorRate, 0) /
          allAgents.length
        : 0

    return {
      totalAgents: this.agents.size,
      activeAgents: this.getActiveAgents().length,
      totalTasks: this.tasks.size,
      pendingTasks: allTasks.filter((t) => t.status === 'pending').length,
      completedTasks: allTasks.filter((t) => t.status === 'completed').length,
      failedTasks: allTasks.filter((t) => t.status === 'failed').length,
      averageSuccessRate: Math.round(avgSuccessRate * 100) / 100,
      averageErrorRate: Math.round(avgErrorRate * 100) / 100,
    }
  }
}

// Global instance
export const agentRegistry = new AgentRegistry()

// Legacy API compatibility
export const AGENT_REGISTRY = AGENT_TEMPLATES

export function getAgent(agentId: string): Agent | undefined {
  return agentRegistry.getAgent(agentId) || undefined
}

export function getAgentsByType(type: string): Agent[] {
  return agentRegistry.getAgentsByType(type)
}

export function getAllAgentIds(): string[] {
  return agentRegistry.getAllAgents().map((a) => a.id)
}

export function getEnabledAgents(): Agent[] {
  return agentRegistry.getAllAgents().filter((a) => a.enabled)
}

export function calculateNextRun(agent: Agent): Date {
  if (!agent.interval) return new Date()
  const lastRun = agent.lastRun?.toDate?.() || new Date()
  return new Date(lastRun.getTime() + agent.interval * 1000)
}
