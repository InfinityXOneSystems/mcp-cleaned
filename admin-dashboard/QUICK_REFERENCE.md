# Admin Dashboard - Quick Reference Card

## Essential Commands

### Development
```bash
npm run dev              # Start dev server (localhost:5173)
npm run build           # Build for production
firebase emulators:start # Start Firebase emulator
```

### Testing
```bash
npm run test            # Run all tests
npm run test:coverage   # Generate coverage report
npm run test:e2e        # Run end-to-end tests
```

### Deployment
```bash
npm run build
firebase deploy         # Deploy to Firebase Hosting
# OR
docker build -t dashboard:latest .
gcloud run deploy admin-dashboard ...
```

---

## Key Files & Locations

| Purpose | Location |
|---------|----------|
| Main App | `src/App.tsx` |
| Dashboard Component | `src/components/Dashboard.tsx` |
| Firebase Config | `src/lib/firebase.ts` |
| Auth Service | `src/services/auth.ts` |
| Firestore Service | `src/services/firestore.ts` |
| Agent Registry | `src/agents/registry.ts` |
| Firebase Rules | `firebase/firestore.rules` |
| Environment Config | `.env.local` |

---

## Environment Variables

```env
# Firebase
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_PROJECT_ID=infinity-x-one-systems

# Development
VITE_USE_FIREBASE_EMULATORS=true
```

---

## Service API Quick Reference

### Authentication
```typescript
import { authService } from '@/services/auth'

await authService.login(email, password)
await authService.signup(email, password, name, role)
await authService.logout()
const user = await authService.getCurrentUser()
await authService.hasPermission(uid, 'manage_agents')
```

### Firestore
```typescript
import { 
  agentService, 
  propertyService, 
  predictionService 
} from '@/services/firestore'

// Get data
const agents = await agentService.getAllAgents()
const properties = await propertyService.getProperties()

// Real-time subscription
agentService.subscribeToAgents((agents) => {
  setAgents(agents)
})

// Create
const id = await agentService.createAgent({ /* config */ })

// Update
await agentService.updateAgent(id, { status: 'active' })

// Delete
await agentService.deleteAgent(id)
```

### Agent Registry
```typescript
import { agentRegistry, AGENT_TEMPLATES } from '@/agents/registry'

// Register agent
const agentId = agentRegistry.registerFromTemplate('PROPERTY_SCRAPER')

// Create task
const taskId = agentRegistry.createTask(agentId, { /* input */ })

// Update status
agentRegistry.updateAgentStatus(agentId, 'running')

// Record metrics
agentRegistry.recordRun(agentId, true, 2500) // success, 2.5s duration

// Get stats
const stats = agentRegistry.getStats()
```

---

## Component Templates

### Using Firestore Data
```typescript
import { useEffect, useState } from 'react'
import { agentService } from '@/services/firestore'

export function MyComponent() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = agentService.subscribeToAgents((agents) => {
      setAgents(agents)
      setLoading(false)
    })
    return () => unsubscribe()
  }, [])

  if (loading) return <div>Loading...</div>
  return <div>{agents.map(a => <p key={a.id}>{a.name}</p>)}</div>
}
```

### Using Authentication
```typescript
import { useEffect, useState } from 'react'
import { authService } from '@/services/auth'
import { auth } from '@/lib/firebase'

export function ProtectedComponent() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    const unsubscribe = authService.onAuthStateChanged((user) => {
      setUser(user)
    })
    return () => unsubscribe()
  }, [])

  if (!user) return <div>Please log in</div>
  return <div>Welcome {user.email}</div>
}
```

---

## Firestore Collections

| Collection | Contains |
|-----------|----------|
| `users` | User accounts & settings |
| `agents` | Agent configurations |
| `agent_tasks` | Task history |
| `properties` | Real estate data |
| `loan_signals` | Mortgage opportunities |
| `predictions` | ML predictions |
| `chat` | Messages |
| `notifications` | Alerts |

---

## Agent Templates

| Template | Type | Interval |
|----------|------|----------|
| PROPERTY_SCRAPER | scraper | 6h |
| MORTGAGE_MONITOR | crawler | 1h |
| SENTIMENT_ANALYZER | analyst | 4h |
| VALUE_PREDICTOR | prediction | 24h |
| RISK_ASSESSOR | analyst | 12h |
| NOTIFICATION_SERVICE | validator | 1m |
| DATA_QUALITY | validator | 3h |
| VISION_CORTEX | analyst | 10m |

---

## User Roles & Permissions

| Role | Permissions |
|------|------------|
| **Admin** | All operations |
| **Operator** | Manage agents, properties, tasks |
| **Analyst** | Create predictions, analyze data |
| **Viewer** | Read-only access |

---

## Common Queries

### Get Active Agents
```typescript
const active = agentRegistry.getActiveAgents()
// or
const active = await agentService.getActiveAgents()
```

### Get Property by City
```typescript
const properties = await propertyService.getPropertiesByCity('Miami')
```

### Get Pending Tasks
```typescript
const pending = agentRegistry.getPendingTasks()
```

### Get Predictions for Property
```typescript
const predictions = await predictionService.getPredictionsForProperty(propertyId)
```

---

## Error Handling

```typescript
try {
  const agents = await agentService.getAllAgents()
} catch (error) {
  console.error('Failed to fetch agents:', error.message)
  // Handle error
}
```

---

## Firebase Emulator URLs

| Service | URL |
|---------|-----|
| Emulator UI | http://localhost:4000 |
| Auth | http://localhost:9099 |
| Firestore | http://localhost:8080 |
| Storage | http://localhost:9199 |
| Functions | http://localhost:5001 |

---

## Troubleshooting Quick Fixes

### Can't connect to Firestore
```bash
lsof -i :8080
kill -9 <PID>
firebase emulators:start
```

### Build fails
```bash
npm run clean
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Firebase config issues
1. Check `.env.local` has all required keys
2. Verify `firebase.json` exists
3. Run `firebase login` again

### Memory issues
```bash
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

---

## Performance Tips

1. **Use subscriptions for real-time data** instead of polling
2. **Implement pagination** for large datasets
3. **Lazy load components** with React.lazy()
4. **Batch database operations** when possible
5. **Use indexes** for complex Firestore queries
6. **Monitor query performance** in Firebase Console

---

## Documentation Links

- [README](./README.md) - Project overview
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Deployment steps
- [API Documentation](./API_DOCUMENTATION.md) - Complete API reference
- [Firestore Schema](./FIRESTORE_SCHEMA.md) - Database structure
- [Integration Guide](./INTEGRATION_GUIDE.md) - Integration patterns
- [Testing Guide](./TESTING_GUIDE.md) - Testing strategies
- [Project Summary](./PROJECT_SUMMARY.md) - Complete overview

---

## Useful Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Vite Documentation](https://vitejs.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)

---

## Support Channels

1. Check relevant documentation file
2. Review troubleshooting sections
3. Check error message in browser console
4. Review Firebase Console logs
5. Contact development team

---

**Last Updated**: 2024  
**Version**: 1.0.0

**Print this page for quick reference during development!**
