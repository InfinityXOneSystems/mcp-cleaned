# Firestore Schema Documentation

## Collections Overview

### 1. Users Collection
Path: `/users/{userId}`

```typescript
interface User {
  uid: string;
  email: string;
  displayName: string;
  photoURL?: string;
  role: 'admin' | 'operator' | 'analyst' | 'viewer';
  permissions: string[];
  createdAt: Timestamp;
  lastSignIn: Timestamp;
  settings: {
    theme: 'dark' | 'light';
    notifications: boolean;
    emailAlerts: boolean;
  };
}
```

### 2. Agents Collection
Path: `/agents/{agentId}`

```typescript
interface Agent {
  id: string;
  name: string;
  description: string;
  type: 'scraper' | 'analyzer' | 'predictor' | 'monitor';
  status: 'active' | 'inactive' | 'error' | 'paused';
  config: {
    apiKey?: string;
    endpoint: string;
    headers?: Record<string, string>;
    retryAttempts: number;
    timeoutMs: number;
  };
  lastRun: Timestamp;
  nextRun: Timestamp;
  schedule: string; // cron format
  metrics: {
    totalRuns: number;
    successfulRuns: number;
    failedRuns: number;
    averageDuration: number;
  };
  createdBy: string;
  updatedAt: Timestamp;
}
```

### 3. Agent Tasks Collection
Path: `/agent_tasks/{taskId}`

```typescript
interface AgentTask {
  id: string;
  agentId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  startTime: Timestamp;
  endTime?: Timestamp;
  duration?: number; // milliseconds
  priority: number;
  retryCount: number;
  createdAt: Timestamp;
}
```

### 4. Properties Collection
Path: `/properties/{propertyId}`

```typescript
interface Property {
  id: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  county: string;
  
  basicInfo: {
    bedrooms: number;
    bathrooms: number;
    sqft: number;
    yearBuilt: number;
    propertyType: string;
    owner: string;
  };

  valuationHistory: {
    currentEstimate: number;
    previousEstimate: number;
    assessedValue: number;
    lastAssessmentDate: Timestamp;
    trend: 'up' | 'down' | 'stable';
    trendPercentage: number;
  };

  financialMetrics: {
    marketValue: number;
    rentalIncome?: number;
    expenseRatio?: number;
    capRate?: number;
  };

  riskAssessment: {
    score: number; // 0-100
    category: 'low' | 'medium' | 'high';
    factors: string[];
  };

  loanEligibility: {
    eligible: boolean;
    maxLoanAmount: number;
    ltv: number;
    dscr?: number;
  };

  metadata: {
    lastUpdated: Timestamp;
    dataSourceId: string;
    confidence: number; // 0-100
    sources: string[];
  };
}
```

### 5. Loan Signals Collection
Path: `/loan_signals/{signalId}`

```typescript
interface LoanSignal {
  id: string;
  propertyId: string;
  signalType: 'mortgage_activity' | 'tax_assessment' | 'property_sale' | 'lien_filing';
  
  details: {
    description: string;
    date: Timestamp;
    amount?: number;
    confidence: number;
  };

  impact: {
    riskAdjustment: number; // -100 to 100
    opportunityScore: number;
  };

  source: {
    agentId: string;
    dataProvider: string;
    url?: string;
  };

  processed: boolean;
  createdAt: Timestamp;
}
```

### 6. Predictions Collection
Path: `/predictions/{predictionId}`

```typescript
interface Prediction {
  id: string;
  propertyId: string;
  predictionType: 'price' | 'risk' | 'demand' | 'return';
  
  forecast: {
    value: number;
    confidence: number;
    timeframe: string; // e.g., "30-days", "90-days"
  };

  actual?: {
    value: number;
    variance: number;
    date: Timestamp;
  };

  model: {
    name: string;
    version: string;
    features: string[];
  };

  createdAt: Timestamp;
  updatedAt: Timestamp;
  accuracy?: number; // after actual is recorded
}
```

### 7. Market Sentiment Collection
Path: `/market_sentiment/{sentimentId}`

```typescript
interface MarketSentiment {
  id: string;
  region: string;
  timestamp: Timestamp;
  
  sentiment: {
    score: number; // -100 to 100
    trend: 'bullish' | 'bearish' | 'neutral';
  };

  indicators: {
    salesVolume: number;
    priceChange: number;
    daysOnMarket: number;
    pricePerSqft: number;
  };

  sources: {
    agentId: string;
    dataPoints: number;
    confidence: number;
  };
}
```

### 8. Chat Messages Collection
Path: `/chat/{messageId}`

```typescript
interface ChatMessage {
  id: string;
  userId: string;
  content: string;
  role: 'user' | 'assistant';
  
  context?: {
    propertyId?: string;
    agentId?: string;
    taskId?: string;
  };

  metadata: {
    model: string;
    tokens: number;
    confidence?: number;
  };

  spoken?: string; // TTS output
  createdAt: Timestamp;
}
```

### 9. Notifications Collection
Path: `/notifications/{notificationId}`

```typescript
interface Notification {
  id: string;
  userId: string;
  type: 'alert' | 'update' | 'task' | 'prediction';
  
  content: {
    title: string;
    message: string;
    actionUrl?: string;
  };

  priority: 'low' | 'normal' | 'high' | 'critical';
  read: boolean;
  createdAt: Timestamp;
  expiresAt?: Timestamp;
}
```

### 10. System Collection
Path: `/system/{document}`

```typescript
interface SystemState {
  agentHealthCheck: {
    timestamp: Timestamp;
    activeAgents: number;
    failedAgents: string[];
  };

  performanceMetrics: {
    averageResponseTime: number;
    successRate: number;
    errorRate: number;
  };

  deploymentInfo: {
    version: string;
    environment: 'development' | 'staging' | 'production';
    lastDeployment: Timestamp;
  };

  maintenanceMode: {
    enabled: boolean;
    message?: string;
    startTime?: Timestamp;
    endTime?: Timestamp;
  };
}
```

## Indexes Required

### Composite Indexes

```yaml
# Properties - for complex queries
collections/properties:
  - fields:
      - city
      - status
      - createdAt (Descending)

# Loan Signals - by property and date
collections/loan_signals:
  - fields:
      - propertyId
      - createdAt (Descending)

# Predictions - by property and type
collections/predictions:
  - fields:
      - propertyId
      - predictionType
      - createdAt (Descending)

# Agent Tasks - by agent and status
collections/agent_tasks:
  - fields:
      - agentId
      - status
      - createdAt (Descending)
```

## Data Migration Scripts

See `scripts/migrate-data.ts` for bulk data operations.

## Security Rules

- Admin: Full read/write access
- Operator: Read all, write agents/tasks
- Analyst: Read all, write predictions
- Viewer: Read-only access

All writes are audited via Cloud Logging.
