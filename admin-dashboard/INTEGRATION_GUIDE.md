# Admin Dashboard - Complete Integration Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Infinity X Admin Dashboard                       │
│  (React + TypeScript + Tailwind CSS + Vite)             │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┬────────────┬──────────┬────────────┐   │
│  │  Dashboard  │   Agents   │ Properties│Predictions│   │
│  │   Registry  │   Manager  │  Manager  │   Engine  │   │
│  └─────────────┴────────────┴──────────┴────────────┘   │
│                      │                                    │
│                      ▼                                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │     Firebase Backend (Firestore + Auth)         │   │
│  │  • Authentication & Authorization               │   │
│  │  • Real-time Data Synchronization               │   │
│  │  • Cloud Functions                              │   │
│  │  • Cloud Storage                                │   │
│  └──────────────────────────────────────────────────┘   │
│                      │                                    │
│                      ▼                                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Backend Services (Python/FastAPI)         │   │
│  │  • Agent Execution Engine                       │   │
│  │  • ML Prediction Models                         │   │
│  │  • Data Processing Pipeline                     │   │
│  │  • Real Estate Intelligence                     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Integration Points

### 1. Firebase Integration

#### Authentication
```typescript
import { authService } from '@/services/auth'

// Login
const user = await authService.login(email, password)

// Check permissions
const canManageAgents = await authService.hasPermission(uid, 'manage_agents')

// Subscribe to auth state
authService.onAuthStateChanged((user) => {
  if (user) {
    // Update UI
  }
})
```

#### Firestore Data
```typescript
import { agentService, propertyService, predictionService } from '@/services/firestore'

// Get data
const agents = await agentService.getAllAgents()
const properties = await propertyService.getProperties()

// Real-time updates
agentService.subscribeToAgents((agents) => {
  setAgents(agents)
})
```

### 2. Agent System Integration

#### Agent Registry
```typescript
import { agentRegistry, AGENT_TEMPLATES } from '@/agents/registry'

// Register agent from template
const agentId = agentRegistry.registerFromTemplate('PROPERTY_SCRAPER')

// Create task
const taskId = agentRegistry.createTask(agentId, {
  keywords: ['Miami', 'real-estate'],
  filters: { priceRange: [300000, 500000] }
})

// Monitor execution
agentRegistry.recordRun(agentId, true, 2500) // success, 2.5s
```

#### Agent Communication
```typescript
// Call backend agent
const response = await fetch('http://localhost:8000/agent/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    agentId: 'property-scraper-1',
    taskId: taskId,
    params: { /* task parameters */ }
  })
})

const result = await response.json()
```

### 3. Backend Service Integration

#### FastAPI Endpoints
```python
# Backend: omni_gateway.py or intelligence_endpoints.py

@app.post("/agent/execute")
async def execute_agent(request: AgentExecutionRequest):
    """Execute an agent task"""
    agent = get_agent(request.agentId)
    result = await agent.execute(request.params)
    return {
        "taskId": request.taskId,
        "status": "completed",
        "output": result
    }

@app.get("/agent/{agentId}/status")
async def get_agent_status(agentId: str):
    """Get agent status and metrics"""
    agent = get_agent(agentId)
    return {
        "status": agent.status,
        "metrics": agent.metrics,
        "lastRun": agent.lastRun
    }
```

#### Data Pipeline
```python
# Real-time data updates to Firestore
async def update_property_data(property_id: str, data: dict):
    """Update property data in Firestore"""
    await db.collection('properties').document(property_id).update({
        **data,
        'lastUpdated': timestamp.now()
    })
```

### 4. Real-time Synchronization

#### Client-side Subscriptions
```typescript
// Subscribe to agent updates
const unsubscribe = agentService.subscribeToAgents((agents) => {
  // Update UI with latest agents
  dispatch(setAgents(agents))
})

// Cleanup on unmount
useEffect(() => {
  return () => unsubscribe()
}, [])
```

#### Server-side Updates
```python
# Backend pushes updates via Firestore
def on_agent_status_change(agent_id: str, new_status: str):
    """Update agent status in Firestore"""
    agents_ref.document(agent_id).update({
        'status': new_status,
        'updatedAt': timestamp.now()
    })
```

### 5. Authentication & Authorization Flow

```
User Login
    ↓
Firebase Auth (Email/Password)
    ↓
JWT Token Generated
    ↓
User Document Loaded from Firestore
    ↓
Role & Permissions Cached
    ↓
Firestore Rules Check Access
    ↓
Dashboard Unlocked
```

## Component Integration Examples

### Dashboard Component
```typescript
import { useEffect, useState } from 'react'
import { agentService } from '@/services/firestore'
import { useAuth } from '@/hooks/useAuth'

export function Dashboard() {
  const { user } = useAuth()
  const [agents, setAgents] = useState([])
  const [stats, setStats] = useState(null)

  useEffect(() => {
    // Subscribe to agent updates
    const unsubscribe = agentService.subscribeToAgents((agents) => {
      setAgents(agents)
      
      // Calculate stats
      const stats = {
        total: agents.length,
        active: agents.filter(a => a.status === 'active').length,
        successRate: agents.reduce((sum, a) => sum + a.metrics.successRate, 0) / agents.length
      }
      setStats(stats)
    })

    return () => unsubscribe()
  }, [])

  return (
    <div>
      <h1>Dashboard - Welcome {user?.displayName}</h1>
      {stats && (
        <div>
          <p>Total Agents: {stats.total}</p>
          <p>Active: {stats.active}</p>
          <p>Success Rate: {stats.successRate.toFixed(2)}%</p>
        </div>
      )}
    </div>
  )
}
```

### Agent Registry Component
```typescript
import { agentRegistry, AGENT_TEMPLATES } from '@/agents/registry'
import { agentService } from '@/services/firestore'

export function AgentRegistry() {
  const [agents, setAgents] = useState([])

  const handleRegister = async (templateKey: string) => {
    // Create agent from template
    const agentId = agentRegistry.registerFromTemplate(templateKey)
    
    // Save to Firestore
    const template = AGENT_TEMPLATES[templateKey]
    await agentService.createAgent({
      ...template,
      id: agentId,
    })
  }

  const handleStartAgent = async (agentId: string) => {
    await agentService.updateAgent(agentId, { status: 'active' })
    
    // Call backend to actually start agent
    await fetch(`http://localhost:8000/agent/${agentId}/start`, {
      method: 'POST'
    })
  }

  return (
    <div>
      <h2>Agent Registry</h2>
      {Object.entries(AGENT_TEMPLATES).map(([key, template]) => (
        <div key={key}>
          <h3>{template.name}</h3>
          <p>{template.description}</p>
          <button onClick={() => handleRegister(key)}>Register</button>
        </div>
      ))}
    </div>
  )
}
```

## Deployment Integration

### Environment Setup

#### Development
```bash
# .env.local
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_PROJECT_ID=...
VITE_USE_FIREBASE_EMULATORS=true
VITE_API_URL=http://localhost:8000
```

#### Production
```bash
# .env.production
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_PROJECT_ID=...
VITE_USE_FIREBASE_EMULATORS=false
VITE_API_URL=https://api.infinityxone.com
```

### Firebase Deployment

```bash
# Deploy hosting
firebase deploy --only hosting

# Deploy Firestore rules
firebase deploy --only firestore:rules

# Deploy Cloud Functions
firebase deploy --only functions
```

### Cloud Run Deployment

```bash
# Build image
docker build -t admin-dashboard:latest .

# Push to registry
gcloud builds submit --tag gcr.io/infinity-x-one-systems/admin-dashboard:latest

# Deploy
gcloud run deploy admin-dashboard \
  --image gcr.io/infinity-x-one-systems/admin-dashboard:latest \
  --platform managed \
  --region us-central1
```

## API Contract Examples

### Create Agent Task
```typescript
// Client
const taskId = agentRegistry.createTask('property-scraper-1', {
  keywords: ['Miami'],
  filters: { minPrice: 300000 }
})

// Backend receives
{
  "agentId": "property-scraper-1",
  "taskId": "task-xxx",
  "input": {
    "keywords": ["Miami"],
    "filters": { "minPrice": 300000 }
  }
}

// Backend responds
{
  "success": true,
  "taskId": "task-xxx",
  "estimatedDuration": 45000
}
```

### Update Prediction
```typescript
// Client
await predictionService.recordActual(predictionId, 485000, 1.04)

// Firestore update
{
  "actual": {
    "value": 485000,
    "variance": 1.04,
    "date": Timestamp.now()
  },
  "accuracy": 96,
  "updatedAt": Timestamp.now()
}
```

## Error Handling & Recovery

### Network Error Recovery
```typescript
const withRetry = async (fn: () => Promise<any>, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)))
    }
  }
}

// Usage
const agents = await withRetry(() => agentService.getAllAgents())
```

### Firestore Connection Issues
```typescript
// Automatic reconnection with exponential backoff
const unsubscribe = agentService.subscribeToAgents(
  (agents) => {
    // Update UI
  },
  {
    onError: (error) => {
      console.error('Subscription error:', error)
      // Retry logic automatically handled by Firestore SDK
    }
  }
)
```

## Monitoring & Debugging

### Enable Logging
```typescript
// Enable Firestore logging in development
if (import.meta.env.DEV) {
  import('firebase/firestore').then(({ enableLogging }) => {
    enableLogging(true)
  })
}
```

### Debug Agent Execution
```typescript
// Monitor agent metrics
const stats = agentRegistry.getStats()
console.log('Agent Statistics:', {
  totalAgents: stats.totalAgents,
  activeAgents: stats.activeAgents,
  avgSuccessRate: stats.averageSuccessRate,
  totalTasks: stats.totalTasks,
  pending: stats.pendingTasks
})
```

## Performance Optimization

### Lazy Load Heavy Components
```typescript
import { lazy, Suspense } from 'react'

const PropertyMap = lazy(() => import('./PropertyMap'))
const PredictionChart = lazy(() => import('./PredictionChart'))

<Suspense fallback={<LoadingSpinner />}>
  <PropertyMap />
  <PredictionChart />
</Suspense>
```

### Batch Firestore Updates
```typescript
// Avoid N+1 queries
const agents = await agentService.getAllAgents()
const properties = await propertyService.getProperties()
// All fetched in parallel

// vs
for (const agentId of agentIds) {
  const agent = await agentService.getAgent(agentId) // N queries
}
```

---

**Last Updated**: 2024
**Version**: 1.0.0
