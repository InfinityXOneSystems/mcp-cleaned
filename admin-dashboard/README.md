# Infinity X Admin Dashboard

Professional, real-time admin dashboard for the Infinity X Autonomous Intelligence Cockpit.

## Features

### 🔐 Security & Access Control
- Firebase Authentication (Email/Password)
- Role-based access control (RBAC)
  - Admin: Full system access
  - Operator: Agent & task management
  - Analyst: Data analysis & predictions
  - Viewer: Read-only access
- Real-time permission verification
- Secure session management

### 🤖 Agent Management
- Real-time agent registry
- Task scheduling & execution
- Performance metrics & analytics
- Agent health monitoring
- Automated task queue management
- Multi-agent coordination

### 🏠 Real Estate Intelligence
- Property discovery & tracking
- Valuation history & trends
- Loan signal detection
- Risk assessment scoring
- Market sentiment analysis
- Geographic property filtering

### 💰 Financial Predictions
- ML-powered price predictions
- Risk forecasting
- Demand analysis
- Return on investment (ROI) calculations
- Prediction vs. actual tracking
- Model performance metrics

### 💬 AI Conversation
- Real-time chat interface
- Context-aware responses
- ChatGPT integration
- Voice input/output (TTS)
- Message history
- Smart suggestions

### 📊 Advanced Analytics
- Real-time data visualization
- Financial graphs (Vega-Lite, ECharts)
- Predictions vs. actuals comparison
- Agent performance dashboards
- Market trend analysis
- Exportable reports

### 🔄 Real-time Updates
- Live WebSocket connections
- Automatic data synchronization
- Push notifications
- Activity feeds
- Status indicators

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 4
- **Styling**: Tailwind CSS 3
- **State Management**: Context API + React Hooks
- **UI Components**: Custom built with shadcn/ui patterns
- **Animations**: Framer Motion
- **Charts**: Vega-Lite, ECharts
- **HTTP Client**: Axios with interceptors

### Backend
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth
- **Storage**: Firebase Cloud Storage
- **Functions**: Firebase Cloud Functions
- **Hosting**: Firebase Hosting / Cloud Run
- **Logging**: Cloud Logging & Sentry

### Development
- **Language**: TypeScript 5
- **Linter**: ESLint
- **Formatter**: Prettier
- **Testing**: Vitest + React Testing Library
- **Debugging**: Chrome DevTools + Firebase Emulator

## Project Structure

```
admin-dashboard/
├── src/
│   ├── components/        # React components
│   │   ├── Dashboard.tsx
│   │   ├── AgentRegistry.tsx
│   │   ├── PropertyMap.tsx
│   │   ├── Predictions.tsx
│   │   └── ChatInterface.tsx
│   ├── services/          # Backend services
│   │   ├── firebase.ts    # Firestore CRUD
│   │   ├── auth.ts        # Authentication
│   │   ├── agents.ts      # Agent management
│   │   └── properties.ts  # Real estate
│   ├── lib/               # Utilities
│   │   ├── firebase.ts    # Firebase init
│   │   ├── theme.tsx      # Theme config
│   │   └── utils.ts       # Helpers
│   ├── types/             # TypeScript definitions
│   │   ├── index.ts
│   │   └── api.ts
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts
│   │   └── useFirestore.ts
│   ├── styles/            # Global styles
│   ├── App.tsx            # Main app component
│   └── main.tsx           # Entry point
├── public/                # Static assets
├── firebase/              # Firebase config
│   ├── firestore.rules    # Security rules
│   ├── storage.rules      # Storage rules
│   └── functions/         # Cloud Functions
├── tests/                 # Test files
├── .env.example           # Environment template
├── vite.config.ts         # Vite config
├── tailwind.config.ts     # Tailwind config
├── tsconfig.json          # TypeScript config
├── firebase.json          # Firebase config
├── package.json           # Dependencies
├── DEPLOYMENT_GUIDE.md    # Deployment docs
├── API_DOCUMENTATION.md   # API reference
└── FIRESTORE_SCHEMA.md    # Database schema
```

## Getting Started

### Prerequisites
- Node.js 18+
- npm 9+
- Firebase account
- Google Cloud project

### Installation

```bash
cd admin-dashboard
npm install
```

### Configuration

```bash
# Copy environment template
cp .env.example .env.local

# Edit .env.local with your Firebase config
nano .env.local
```

### Local Development

```bash
# Start development server
npm run dev

# In another terminal, start Firebase Emulator
firebase emulators:start
```

Access at `http://localhost:5173`

### Build

```bash
npm run build
```

### Deploy

```bash
# Deploy to Firebase Hosting
firebase deploy --only hosting

# Deploy everything
firebase deploy
```

## Environment Variables

See [.env.example](.env.example) for complete list:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_MEASUREMENT_ID=

# Development
VITE_USE_FIREBASE_EMULATORS=true
```

## Documentation

- **[Deployment Guide](./DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[API Documentation](./API_DOCUMENTATION.md)** - Service & API reference
- **[Firestore Schema](./FIRESTORE_SCHEMA.md)** - Database structure & rules
- **[Firebase Rules](./firebase/firestore.rules)** - Security rules

## Scripts

```bash
# Development
npm run dev          # Start dev server
npm run dev:debug   # Dev with debugging

# Building
npm run build       # Production build
npm run build:prod  # Optimized build

# Testing
npm run test        # Run tests
npm run test:ui     # Test UI
npm run test:coverage # Coverage report

# Linting
npm run lint        # Run ESLint
npm run lint:fix    # Fix linting issues
npm run format      # Format with Prettier

# Firebase
npm run firebase:login    # Login to Firebase
npm run firebase:emulate  # Start emulator
npm run firebase:deploy   # Deploy to Firebase
npm run firebase:logs     # View logs

# Database
npm run db:seed     # Seed test data
npm run db:migrate  # Run migrations
npm run db:status   # Migration status
```

## Authentication

### Login Flow
1. User enters email & password
2. Firebase authenticates credentials
3. JWT token generated
4. User role loaded from Firestore
5. Permissions cached locally
6. Dashboard unlocked

### Logout
- Clear local token
- Clear Firestore cache
- Redirect to login

### Role Permissions

| Role | Permissions |
|------|-------------|
| **Admin** | manage_agents, manage_users, manage_properties, manage_predictions, view_all_data, export_data, manage_system |
| **Operator** | manage_agents, manage_properties, create_tasks, view_all_data, export_data |
| **Analyst** | view_all_data, create_predictions, analyze_data, view_reports |
| **Viewer** | view_all_data, view_reports |

## Real-time Features

### Firestore Subscriptions
```typescript
// Auto-resubscribe on connection loss
const unsubscribe = agentService.subscribeToAgents((agents) => {
  setAgents(agents)
})
```

### WebSocket Connections
- Automatic reconnection with exponential backoff
- Message queuing during disconnection
- Real-time notification system

## Performance Optimization

- Code splitting by route
- Lazy loading of components
- Image optimization
- CSS minification
- JavaScript minification
- Efficient Firestore queries with indexing
- Offline support with caching

## Security Best Practices

- ✓ HTTPS only in production
- ✓ Content Security Policy (CSP)
- ✓ CORS configuration
- ✓ Firestore security rules
- ✓ API key restrictions
- ✓ Environment variable protection
- ✓ Automatic session timeout
- ✓ XSS & CSRF protection

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### Emulator Issues
```bash
# Kill existing emulator processes
lsof -i :8080 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Restart emulator
firebase emulators:start
```

### Build Errors
```bash
# Clear cache
npm run clean

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Firebase Connection
- Check `.env.local` configuration
- Verify Firebase project exists
- Check firebaserc file
- Clear browser cache

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for more troubleshooting.

## Contributing

1. Create feature branch (`git checkout -b feature/amazing-feature`)
2. Commit changes (`git commit -m 'Add amazing feature'`)
3. Push to branch (`git push origin feature/amazing-feature`)
4. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

- 📖 [Firebase Documentation](https://firebase.google.com/docs)
- 🔗 [React Documentation](https://react.dev)
- 🎨 [Tailwind Documentation](https://tailwindcss.com/docs)
- 🚀 [Vite Documentation](https://vitejs.dev)

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced reporting engine
- [ ] Custom dashboard layouts
- [ ] Integration with CRM systems
- [ ] Advanced ML model deployment
- [ ] Multi-language support
- [ ] Dark/Light theme toggle
- [ ] Offline-first capabilities

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintained by**: Infinity X Team
