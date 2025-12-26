/**
 * Core type definitions for Infinity X Admin Dashboard
 */

// User & Auth
export interface User {
  uid: string
  email: string
  displayName: string
  role: 'admin' | 'operator' | 'analyst' | 'viewer'
  avatar?: string
  createdAt: Date
  lastLogin?: Date
}

// Agents
export type AgentType = 
  | 'validator'
  | 'crawler'
  | 'scraper'
  | 'code'
  | 'analyst'
  | 'prediction'
  | 'sentiment'
  | 'vision-cortex'

export interface Agent {
  id: string
  name: string
  type: AgentType
  description: string
  enabled: boolean
  status: 'idle' | 'running' | 'error' | 'paused'
  interval?: number // seconds
  lastRun?: Date
  nextRun?: Date
  errorMessage?: string
  version: string
  config: Record<string, any>
}

export interface AgentTask {
  id: string
  agentId: string
  taskType: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startedAt: Date
  completedAt?: Date
  result?: any
  error?: string
}

// Real Estate Intelligence
export interface RealEstateProperty {
  id: string
  address: string
  city: string
  state: string
  zip: string
  price: number
  estimatedValue?: number
  beds: number
  baths: number
  sqft: number
  yearBuilt: number
  distressScore: number // 0-100
  signals: string[]
  source: string
  discoveredAt: Date
  lastUpdated: Date
}

// Financial Intelligence
export interface LoanSignal {
  id: string
  businessName: string
  borrowerType: 'individual' | 'business' | 'sme'
  loanAmount: number
  purpose: string
  loanType: string
  riskScore: number // 0-100
  urgencyScore: number // 0-100
  confidence: number // 0-1
  signals: string[]
  sourceAgent: string
  discoveredAt: Date
  contactAttempts: number
}

// Market Sentiment
export interface MarketSentiment {
  id: string
  keyword: string
  sentiment: 'bullish' | 'bearish' | 'neutral'
  score: number // -1 to 1
  volume: number
  trend: 'rising' | 'falling' | 'stable'
  sources: string[]
  timestamp: Date
}

// Predictions
export interface Prediction {
  id: string
  target: string // what is being predicted
  metric: string
  currentValue: number
  predictedValue: number
  confidence: number // 0-1
  predictionDate: Date
  horizon: 'short-term' | 'medium-term' | 'long-term'
  model: string
  actualValue?: number
  correct?: boolean
}

// Git/GitHub
export interface RepositoryStatus {
  id: string
  name: string
  owner: string
  url: string
  defaultBranch: string
  lastCommit?: string
  lastCommitTime?: Date
  openIssues: number
  openPRs: number
  status: 'healthy' | 'warning' | 'error'
  agents?: string[] // agent commits
}

// Notifications
export interface Notification {
  id: string
  userId: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error' | 'opportunity'
  read: boolean
  actionUrl?: string
  createdAt: Date
  expiresAt?: Date
}

// Dashboard State
export interface DashboardState {
  selectedTimeRange: 'today' | 'week' | 'month' | 'quarter' | 'year' | 'all'
  filters: {
    agentTypes?: AgentType[]
    statuses?: string[]
    confidence?: number // min confidence
  }
  dryRunMode: boolean
  selectedAgents: string[]
}

// Chat/Voice
export interface ChatMessage {
  id: string
  userId: string
  agentId?: string
  message: string
  response?: string
  timestamp: Date
  type: 'user' | 'agent' | 'system'
}

export interface VoiceSession {
  id: string
  userId: string
  status: 'active' | 'ended'
  duration: number // seconds
  transcript?: string
  startedAt: Date
  endedAt?: Date
}

// Graph Data
export interface DataPoint {
  timestamp: Date
  value: number
  actual?: number
  predicted?: number
  confidence?: number
  source?: string
}

export interface GraphConfig {
  title: string
  description?: string
  metric: string
  dataPoints: DataPoint[]
  unit?: string
  confidence?: 'high' | 'medium' | 'low'
}

// System Health
export interface SystemHealth {
  status: 'operational' | 'degraded' | 'error'
  timestamp: Date
  components: {
    firestore: boolean
    cloudRun: boolean
    functions: boolean
    auth: boolean
    storage: boolean
  }
  metrics: {
    activeAgents: number
    totalTasks: number
    errorRate: number
    avgResponseTime: number
  }
}
