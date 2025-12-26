# Admin Dashboard - Testing & QA Guide

## Testing Strategy

```
Unit Tests (60%)
    ├─ Services
    ├─ Utilities
    └─ Hooks

Integration Tests (25%)
    ├─ Firebase Integration
    ├─ API Communication
    └─ Authentication Flow

E2E Tests (15%)
    ├─ User Workflows
    ├─ Agent Management
    └─ Data Operations
```

## Unit Testing

### Service Tests

```typescript
// src/__tests__/services/firestore.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { agentService } from '@/services/firestore'
import * as fs from 'firebase/firestore'

vi.mock('firebase/firestore')

describe('agentService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get all agents', async () => {
    const mockAgents = [
      {
        id: 'agent-1',
        name: 'Test Agent',
        status: 'active',
        metrics: { successRate: 100 }
      }
    ]
    
    vi.spyOn(fs, 'getDocs').mockResolvedValue({
      docs: mockAgents.map(agent => ({
        id: agent.id,
        data: () => agent
      }))
    })

    const agents = await agentService.getAllAgents()
    expect(agents).toHaveLength(1)
    expect(agents[0].name).toBe('Test Agent')
  })

  it('should create agent', async () => {
    const agentData = {
      name: 'New Agent',
      type: 'scraper' as const,
      status: 'inactive' as const,
      config: {
        endpoint: 'https://api.example.com',
        retryAttempts: 3,
        timeoutMs: 30000,
      },
      metrics: {
        totalRuns: 0,
        successfulRuns: 0,
        failedRuns: 0,
        averageDuration: 0,
      },
    }

    vi.spyOn(fs, 'setDoc').mockResolvedValue(undefined)
    vi.spyOn(fs, 'doc').mockReturnValue('agent-new')

    const agentId = await agentService.createAgent(agentData)
    expect(agentId).toBeDefined()
  })

  it('should update agent', async () => {
    const updates = { status: 'active' as const }
    
    vi.spyOn(fs, 'updateDoc').mockResolvedValue(undefined)

    await expect(
      agentService.updateAgent('agent-1', updates)
    ).resolves.not.toThrow()
  })

  it('should subscribe to agents', (done) => {
    const mockUnsubscribe = vi.fn()
    vi.spyOn(fs, 'onSnapshot').mockReturnValue(mockUnsubscribe)

    const unsubscribe = agentService.subscribeToAgents((agents) => {
      expect(agents).toBeDefined()
      unsubscribe()
      done()
    })

    expect(unsubscribe).toBe(mockUnsubscribe)
  })
})
```

### Authentication Tests

```typescript
// src/__tests__/services/auth.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { authService } from '@/services/auth'
import * as auth from 'firebase/auth'
import * as firestore from 'firebase/firestore'

vi.mock('firebase/auth')
vi.mock('firebase/firestore')

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should login user', async () => {
    const mockUser = { uid: 'user-123', email: 'test@example.com' }
    vi.spyOn(auth, 'signInWithEmailAndPassword').mockResolvedValue({
      user: mockUser
    })

    const user = await authService.login('test@example.com', 'password')
    expect(user).toEqual(mockUser)
  })

  it('should signup user', async () => {
    const mockUser = {
      uid: 'user-new',
      email: 'newuser@example.com',
      photoURL: null,
    }

    vi.spyOn(auth, 'createUserWithEmailAndPassword').mockResolvedValue({
      user: mockUser
    })
    vi.spyOn(firestore, 'setDoc').mockResolvedValue(undefined)

    const user = await authService.signup(
      'newuser@example.com',
      'password',
      'John Doe',
      'operator'
    )
    expect(user).toEqual(mockUser)
  })

  it('should logout user', async () => {
    vi.spyOn(auth, 'signOut').mockResolvedValue(undefined)

    await expect(authService.logout()).resolves.not.toThrow()
  })

  it('should check permissions', async () => {
    vi.spyOn(firestore, 'getDoc').mockResolvedValue({
      exists: () => true,
      data: () => ({ permissions: ['manage_agents', 'view_all_data'] })
    })

    const hasPermission = await authService.hasPermission('user-123', 'manage_agents')
    expect(hasPermission).toBe(true)

    const noPermission = await authService.hasPermission('user-123', 'manage_users')
    expect(noPermission).toBe(false)
  })
})
```

### Utility Function Tests

```typescript
// src/__tests__/lib/utils.test.ts
import { describe, it, expect } from 'vitest'
import { calculateSuccessRate, formatDuration, formatCurrency } from '@/lib/utils'

describe('utility functions', () => {
  it('should calculate success rate', () => {
    expect(calculateSuccessRate(95, 5)).toBe(95)
    expect(calculateSuccessRate(50, 50)).toBe(50)
    expect(calculateSuccessRate(100, 0)).toBe(100)
  })

  it('should format duration', () => {
    expect(formatDuration(1000)).toBe('1.0s')
    expect(formatDuration(60000)).toBe('1m 0s')
    expect(formatDuration(3661000)).toBe('1h 1m 1s')
  })

  it('should format currency', () => {
    expect(formatCurrency(1000)).toBe('$1,000.00')
    expect(formatCurrency(1000000)).toBe('$1,000,000.00')
    expect(formatCurrency(999.99)).toBe('$999.99')
  })
})
```

## Integration Testing

### Firebase Integration Tests

```typescript
// src/__tests__/integration/firebase.integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { initializeTestEnvironment, assertFails, assertSucceeds } from '@firebase/rules-unit-testing'
import { doc, setDoc, getDoc } from 'firebase/firestore'

let testEnv: any

describe('Firebase Integration', () => {
  beforeAll(async () => {
    testEnv = await initializeTestEnvironment({
      projectId: 'demo-project',
    })
  })

  afterAll(async () => {
    await testEnv.cleanup()
  })

  describe('Firestore Rules', () => {
    it('should allow admin to read all documents', async () => {
      const db = testEnv.authenticatedContext('admin-user', {
        role: 'admin',
      }).firestore()

      const docRef = doc(db, 'agents', 'agent-1')
      await assertSucceeds(getDoc(docRef))
    })

    it('should deny viewer from writing', async () => {
      const db = testEnv.authenticatedContext('viewer-user', {
        role: 'viewer',
      }).firestore()

      const docRef = doc(db, 'agents', 'agent-1')
      await assertFails(setDoc(docRef, { status: 'active' }))
    })

    it('should allow user to read own user doc', async () => {
      const userId = 'user-123'
      const db = testEnv.authenticatedContext(userId).firestore()

      const docRef = doc(db, 'users', userId)
      await assertSucceeds(getDoc(docRef))
    })

    it('should deny user from reading others user doc', async () => {
      const db = testEnv.authenticatedContext('user-123').firestore()

      const docRef = doc(db, 'users', 'user-456')
      await assertFails(getDoc(docRef))
    })
  })

  describe('Authentication', () => {
    it('should persist user session', async () => {
      // Test session persistence across page reloads
      const user = await testEnv.authenticatedContext('test-user').firestore()
      expect(user).toBeDefined()
    })
  })
})
```

### API Communication Tests

```typescript
// src/__tests__/integration/api.integration.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { rest } from 'msw'
import { setupServer } from 'msw/node'

const server = setupServer(
  rest.post('http://localhost:8000/agent/execute', (req, res, ctx) => {
    return res(ctx.json({ taskId: 'task-123', status: 'completed' }))
  }),
  rest.get('http://localhost:8000/agent/:agentId/status', (req, res, ctx) => {
    return res(ctx.json({ status: 'active', metrics: { successRate: 95 } }))
  })
)

beforeEach(() => server.listen())
afterEach(() => server.closeHandler())

describe('Agent API', () => {
  it('should execute agent task', async () => {
    const response = await fetch('http://localhost:8000/agent/execute', {
      method: 'POST',
      body: JSON.stringify({ agentId: 'property-scraper-1' }),
    })
    const data = await response.json()
    expect(data.taskId).toBe('task-123')
    expect(data.status).toBe('completed')
  })

  it('should get agent status', async () => {
    const response = await fetch('http://localhost:8000/agent/agent-1/status')
    const data = await response.json()
    expect(data.status).toBe('active')
    expect(data.metrics.successRate).toBe(95)
  })
})
```

## Component Testing

### Dashboard Component Tests

```typescript
// src/__tests__/components/Dashboard.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Dashboard } from '@/components/Dashboard'
import * as firestoreServices from '@/services/firestore'

vi.mock('@/services/firestore')
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { displayName: 'Test User' }
  })
}))

describe('Dashboard Component', () => {
  it('should render dashboard', () => {
    render(<Dashboard />)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
  })

  it('should load agents on mount', async () => {
    const mockAgents = [
      { id: 'agent-1', name: 'Agent 1', status: 'active' }
    ]

    vi.spyOn(firestoreServices.agentService, 'subscribeToAgents').mockImplementation(
      (callback) => {
        callback(mockAgents as any)
        return () => {}
      }
    )

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument()
    })
  })

  it('should display agent statistics', async () => {
    const mockAgents = [
      {
        id: 'agent-1',
        name: 'Agent 1',
        status: 'active',
        metrics: { successRate: 95 }
      }
    ]

    vi.spyOn(firestoreServices.agentService, 'subscribeToAgents').mockImplementation(
      (callback) => {
        callback(mockAgents as any)
        return () => {}
      }
    )

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/95/)).toBeInTheDocument() // Success rate
    })
  })
})
```

## E2E Testing

### Playwright Tests

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test('should login user', async ({ page }) => {
    await page.goto('http://localhost:5173')
    
    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[type="password"]', 'password')
    await page.click('button:has-text("Login")')

    await expect(page).toHaveURL(/dashboard/)
    await expect(page.locator('text=Welcome')).toBeVisible()
  })

  it('should show error on invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:5173')
    
    await page.fill('input[type="email"]', 'invalid@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.click('button:has-text("Login")')

    await expect(page.locator('text=Invalid credentials')).toBeVisible()
  })
})

// e2e/agent-management.spec.ts
test.describe('Agent Management', () => {
  test('should create and start agent', async ({ page }) => {
    await page.goto('http://localhost:5173/agents')
    
    await page.click('button:has-text("Add Agent")')
    await page.fill('input[name="name"]', 'Test Agent')
    await page.selectOption('select[name="type"]', 'scraper')
    await page.click('button:has-text("Create")')

    await expect(page.locator('text=Test Agent')).toBeVisible()
    
    await page.click('button:has-text("Start")')
    await expect(page.locator('[data-status="running"]')).toBeVisible()
  })

  test('should view agent metrics', async ({ page }) => {
    await page.goto('http://localhost:5173/agents')
    
    await page.click('text=Property Scraper')
    await expect(page.locator('text=Success Rate')).toBeVisible()
    await expect(page.locator('text=Total Runs')).toBeVisible()
  })
})
```

## Performance Testing

### Load Testing

```typescript
// tests/performance/load.test.ts
import { describe, it, expect } from 'vitest'
import { performance } from 'perf_hooks'

describe('Performance Tests', () => {
  it('should fetch agents within 1 second', async () => {
    const start = performance.now()
    await agentService.getAllAgents()
    const duration = performance.now() - start
    
    expect(duration).toBeLessThan(1000)
  })

  it('should create task within 500ms', async () => {
    const start = performance.now()
    agentRegistry.createTask('agent-1', { test: true })
    const duration = performance.now() - start
    
    expect(duration).toBeLessThan(500)
  })

  it('should render dashboard within 2 seconds', async () => {
    const start = performance.now()
    render(<Dashboard />)
    const duration = performance.now() - start
    
    expect(duration).toBeLessThan(2000)
  })
})
```

## Testing Commands

```bash
# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test src/__tests__/services/firestore.test.ts

# Run in watch mode
npm run test:watch

# Run E2E tests
npm run test:e2e

# Run E2E with UI
npm run test:e2e -- --ui

# Generate coverage report
npm run test:coverage -- --reporter=html
```

## Coverage Targets

```
Statements   : 80%+
Branches     : 75%+
Functions    : 80%+
Lines        : 80%+
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - run: npm ci
      - run: npm run lint
      - run: npm run test:coverage
      - run: npm run build
      - run: npx playwright install
      - run: npm run test:e2e

      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
```

## Test Data Management

### Seed Data

```typescript
// tests/fixtures/seed.ts
export const SEED_AGENTS = [
  {
    id: 'property-scraper-1',
    name: 'Property Scraper',
    type: 'scraper',
    status: 'active',
    metrics: { successRate: 95, errorRate: 5 }
  },
  {
    id: 'mortgage-monitor-1',
    name: 'Mortgage Monitor',
    type: 'crawler',
    status: 'active',
    metrics: { successRate: 98, errorRate: 2 }
  }
]

export const SEED_PROPERTIES = [
  {
    id: 'prop-1',
    address: '123 Main St',
    city: 'Miami',
    valuationHistory: { currentEstimate: 450000 }
  }
]
```

---

**Last Updated**: 2024
**Version**: 1.0.0
