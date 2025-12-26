# Admin Dashboard - API & Service Documentation

## Overview

The Admin Dashboard consists of:
- **Frontend**: React + TypeScript + Tailwind CSS (Vite)
- **Backend**: Firebase (Firestore, Auth, Functions, Storage)
- **Real-time**: Firebase Realtime Listeners
- **Authentication**: Firebase Auth with custom roles

## Service Layer Architecture

### Core Services

```
src/services/
├── firebase.ts       # Firestore CRUD operations
├── auth.ts           # Authentication & authorization
├── agents.ts         # Agent management
├── properties.ts     # Real estate properties
└── predictions.ts    # Prediction models
```

## Authentication Service

### Interface

```typescript
interface AuthUser {
  uid: string
  email: string | null
  displayName: string | null
  photoURL: string | null
  role: 'admin' | 'operator' | 'analyst' | 'viewer'
  permissions: string[]
}
```

### Methods

#### `login(email: string, password: string): Promise<User>`
Login with email and password.

```typescript
import { authService } from '@/services/auth'

const user = await authService.login('user@example.com', 'password')
```

#### `signup(email, password, displayName, role): Promise<User>`
Create new user account.

```typescript
const user = await authService.signup(
  'newuser@example.com',
  'password123',
  'John Doe',
  'operator'
)
```

#### `logout(): Promise<void>`
Sign out current user.

```typescript
await authService.logout()
```

#### `getCurrentUser(): Promise<AuthUser | null>`
Get current authenticated user.

```typescript
const currentUser = await authService.getCurrentUser()
if (currentUser?.role === 'admin') {
  // Show admin features
}
```

#### `onAuthStateChanged(callback): Unsubscribe`
Subscribe to auth state changes.

```typescript
const unsubscribe = authService.onAuthStateChanged((user) => {
  if (user) {
    console.log('User logged in:', user.email)
  } else {
    console.log('User logged out')
  }
})

// Cleanup
unsubscribe()
```

#### `hasPermission(uid: string, permission: string): Promise<boolean>`
Check if user has specific permission.

```typescript
const canManageAgents = await authService.hasPermission(uid, 'manage_agents')
```

## Firestore Service

Generic CRUD operations for all collections.

### Generic Methods

#### `getDoc<T>(collectionName, docId): Promise<T | null>`
Get single document.

```typescript
const agent = await firestoreService.getDoc<Agent>('agents', 'agent-123')
```

#### `getAllDocs<T>(collectionName, constraints): Promise<T[]>`
Get all documents with optional constraints.

```typescript
import { where, orderBy, limit } from 'firebase/firestore'

const activeAgents = await firestoreService.getAllDocs<Agent>('agents', [
  where('status', '==', 'active'),
  orderBy('createdAt', 'desc'),
  limit(10),
])
```

#### `setDoc<T>(collectionName, docId, data, merge): Promise<void>`
Create or update document.

```typescript
await firestoreService.setDoc('agents', 'agent-123', {
  name: 'Property Scraper',
  status: 'active',
}, merge = true)
```

#### `updateDoc(collectionName, docId, data): Promise<void>`
Update specific fields in document.

```typescript
await firestoreService.updateDoc('agents', 'agent-123', {
  status: 'paused',
  lastRun: new Date(),
})
```

#### `deleteDoc(collectionName, docId): Promise<void>`
Delete document.

```typescript
await firestoreService.deleteDoc('agents', 'agent-123')
```

#### `subscribe<T>(collectionName, constraints, callback): Unsubscribe`
Real-time subscription to collection.

```typescript
const unsubscribe = firestoreService.subscribe<Agent>(
  'agents',
  [orderBy('updatedAt', 'desc')],
  (agents) => {
    console.log('Agents updated:', agents)
  }
)

// Cleanup
unsubscribe()
```

## Agent Service

Specialized agent management.

### Methods

#### `getAllAgents(): Promise<Agent[]>`
Get all agents.

```typescript
const agents = await agentService.getAllAgents()
```

#### `getAgent(agentId: string): Promise<Agent | null>`
Get single agent.

```typescript
const agent = await agentService.getAgent('agent-123')
```

#### `getActiveAgents(): Promise<Agent[]>`
Get only active agents.

```typescript
const active = await agentService.getActiveAgents()
```

#### `createAgent(agent): Promise<string>`
Create new agent.

```typescript
const agentId = await agentService.createAgent({
  name: 'Property Crawler',
  description: 'Scrapes property data',
  type: 'scraper',
  status: 'active',
  config: {
    endpoint: 'https://api.example.com',
    retryAttempts: 3,
    timeoutMs: 30000,
  },
  schedule: '0 */6 * * *', // Every 6 hours
  metrics: {
    totalRuns: 0,
    successfulRuns: 0,
    failedRuns: 0,
    averageDuration: 0,
  },
})
```

#### `updateAgent(agentId, updates): Promise<void>`
Update agent configuration.

```typescript
await agentService.updateAgent('agent-123', {
  status: 'paused',
  'config.timeoutMs': 60000,
})
```

#### `deleteAgent(agentId): Promise<void>`
Delete agent.

```typescript
await agentService.deleteAgent('agent-123')
```

#### `startAgentTask(agentId, taskType): Promise<string>`
Start a new agent task.

```typescript
const taskId = await agentService.startAgentTask(
  'agent-123',
  'scrape_properties'
)
```

#### `getAgentTasks(agentId, limit): Promise<AgentTask[]>`
Get agent's task history.

```typescript
const tasks = await agentService.getAgentTasks('agent-123', 10)
```

#### `subscribeToAgents(callback): Unsubscribe`
Real-time agent updates.

```typescript
const unsubscribe = agentService.subscribeToAgents((agents) => {
  updateAgentList(agents)
})
```

## Real Estate Service

Property management and analysis.

### Methods

#### `getProperties(limit): Promise<RealEstateProperty[]>`
Get properties.

```typescript
const properties = await realEstateService.getProperties(50)
```

#### `getPropertyById(propertyId): Promise<Property | null>`
Get single property.

```typescript
const property = await realEstateService.getPropertyById('prop-123')
```

#### `getPropertiesByCity(city): Promise<Property[]>`
Get properties in specific city.

```typescript
const cityProperties = await realEstateService.getPropertiesByCity('Miami')
```

#### `addProperty(property): Promise<string>`
Add new property.

```typescript
const propertyId = await realEstateService.addProperty({
  address: '123 Main St',
  city: 'Miami',
  state: 'FL',
  zipCode: '33101',
  county: 'Miami-Dade',
  basicInfo: {
    bedrooms: 3,
    bathrooms: 2,
    sqft: 1500,
    yearBuilt: 1990,
    propertyType: 'residential',
    owner: 'John Doe',
  },
  valuationHistory: {
    currentEstimate: 450000,
    previousEstimate: 440000,
    assessedValue: 420000,
    lastAssessmentDate: new Date(),
    trend: 'up',
    trendPercentage: 2.3,
  },
})
```

#### `updateProperty(propertyId, updates): Promise<void>`
Update property.

```typescript
await realEstateService.updateProperty('prop-123', {
  'valuationHistory.currentEstimate': 460000,
})
```

#### `subscribeToProperties(callback): Unsubscribe`
Real-time property updates.

```typescript
const unsubscribe = realEstateService.subscribeToProperties((props) => {
  updatePropertyList(props)
})
```

## Loan Signal Service

Mortgage opportunity detection.

### Methods

#### `getSignals(limit): Promise<LoanSignal[]>`
Get all loan signals.

```typescript
const signals = await loanSignalService.getSignals(100)
```

#### `getUnprocessedSignals(): Promise<LoanSignal[]>`
Get unprocessed opportunities.

```typescript
const newSignals = await loanSignalService.getUnprocessedSignals()
```

#### `addSignal(signal): Promise<string>`
Create new signal.

```typescript
const signalId = await loanSignalService.addSignal({
  propertyId: 'prop-123',
  signalType: 'mortgage_activity',
  details: {
    description: 'New mortgage filing detected',
    date: new Date(),
    amount: 350000,
    confidence: 0.95,
  },
  impact: {
    riskAdjustment: -15,
    opportunityScore: 75,
  },
  source: {
    agentId: 'agent-123',
    dataProvider: 'county_records',
  },
})
```

#### `updateSignal(signalId, updates): Promise<void>`
Update signal.

```typescript
await loanSignalService.updateSignal('signal-123', {
  processed: true,
})
```

#### `markProcessed(signalId): Promise<void>`
Mark signal as processed.

```typescript
await loanSignalService.markProcessed('signal-123')
```

## Prediction Service

ML prediction management.

### Methods

#### `getPredictions(limit): Promise<Prediction[]>`
Get predictions.

```typescript
const predictions = await predictionService.getPredictions(50)
```

#### `getPredictionsForProperty(propertyId): Promise<Prediction[]>`
Get property predictions.

```typescript
const propertyPredictions = await predictionService.getPredictionsForProperty('prop-123')
```

#### `createPrediction(prediction): Promise<string>`
Create prediction.

```typescript
const predictionId = await predictionService.createPrediction({
  propertyId: 'prop-123',
  predictionType: 'price',
  forecast: {
    value: 480000,
    confidence: 0.87,
    timeframe: '90-days',
  },
  model: {
    name: 'PropertyValuePredictor',
    version: '2.1.0',
    features: ['location', 'size', 'age', 'market_sentiment'],
  },
})
```

#### `updatePrediction(predictionId, updates): Promise<void>`
Update prediction.

```typescript
await predictionService.updatePrediction('pred-123', {
  'forecast.confidence': 0.92,
})
```

#### `recordActual(predictionId, actual, variance): Promise<void>`
Record actual value vs prediction.

```typescript
await predictionService.recordActual('pred-123', 485000, 1.04) // 4% variance
```

## Chat Service

Conversational AI and messaging.

### Methods

#### `getMessages(limit): Promise<ChatMessage[]>`
Get chat history.

```typescript
const messages = await chatService.getMessages(50)
```

#### `createMessage(message): Promise<string>`
Send message.

```typescript
const messageId = await chatService.createMessage({
  userId: 'user-123',
  content: 'What is the risk score for property 123?',
  role: 'user',
  context: {
    propertyId: 'prop-123',
  },
})
```

#### `subscribeToMessages(callback): Unsubscribe`
Real-time message updates.

```typescript
const unsubscribe = chatService.subscribeToMessages((messages) => {
  setMessages(messages)
})
```

## Error Handling

All services throw errors that should be caught:

```typescript
try {
  const agent = await agentService.getAgent('agent-123')
} catch (error) {
  console.error('Failed to fetch agent:', error.message)
  // Handle error
}
```

## Real-time Updates Pattern

```typescript
useEffect(() => {
  // Subscribe
  const unsubscribe = agentService.subscribeToAgents((agents) => {
    setAgents(agents)
  })

  // Cleanup on unmount
  return () => unsubscribe()
}, [])
```

## Query Constraints

Common query patterns:

```typescript
import { where, orderBy, limit, startAfter, endBefore } from 'firebase/firestore'

// Filter
where('status', '==', 'active')
where('score', '>', 75)
where('city', 'in', ['Miami', 'Orlando'])

// Ordering
orderBy('createdAt', 'desc')

// Pagination
limit(10)
startAfter(lastDoc)
endBefore(firstDoc)
```

---

**Last Updated**: 2024
**Version**: 1.0.0
