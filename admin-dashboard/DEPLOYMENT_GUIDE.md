# Admin Dashboard - Complete Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Firebase Configuration](#firebase-configuration)
4. [Environment Variables](#environment-variables)
5. [Firebase Emulator](#firebase-emulator)
6. [Production Deployment](#production-deployment)
7. [Cloud Run Deployment](#cloud-run-deployment)
8. [Database Migrations](#database-migrations)
9. [Monitoring & Logging](#monitoring--logging)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- Node.js 18+ and npm 9+
- Firebase CLI 11+
- Google Cloud SDK
- Docker (for Cloud Run)
- Git

## Local Development Setup

### 1. Install Dependencies

```bash
cd admin-dashboard
npm install
```

### 2. Setup Firebase Project

```bash
# Login to Firebase
firebase login

# Link to your Firebase project
firebase use infinity-x-one-systems
```

### 3. Copy Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local` with your Firebase configuration:

```env
# Firebase Configuration
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=infinity-x-one-systems.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=infinity-x-one-systems
VITE_FIREBASE_STORAGE_BUCKET=infinity-x-one-systems.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=896380409704
VITE_FIREBASE_APP_ID=1:896380409704:web:...
VITE_FIREBASE_MEASUREMENT_ID=G-...

# Development
VITE_USE_FIREBASE_EMULATORS=true
NODE_ENV=development
VITE_API_URL=http://localhost:5173
```

### 4. Run Development Server

```bash
npm run dev
```

Access the dashboard at `http://localhost:5173`

## Firebase Configuration

### Create Firebase Project

```bash
# Using Firebase Console or:
firebase projects:create infinity-x-one-systems --display-name "Infinity X Admin Dashboard"
```

### Enable Required Services

In Firebase Console:
- ✓ Authentication (Email/Password)
- ✓ Firestore Database
- ✓ Cloud Storage
- ✓ Cloud Functions
- ✓ Analytics
- ✓ Cloud Logging

### Initialize Firebase Services

```bash
firebase init
# Select: Authentication, Firestore, Functions, Hosting, Storage
```

## Environment Variables

### Development (.env.local)

```env
# Firebase
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_MEASUREMENT_ID=

# Options
VITE_USE_FIREBASE_EMULATORS=true
VITE_LOG_LEVEL=debug
```

### Production (.env.production)

```env
# Firebase (Production Project)
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
VITE_FIREBASE_MEASUREMENT_ID=

# Options
VITE_USE_FIREBASE_EMULATORS=false
VITE_LOG_LEVEL=warn
```

## Firebase Emulator

### Start Emulator Suite

```bash
firebase emulators:start --import=./emulator-data --export-on-exit
```

Emulator URLs:
- **Firebase Emulator UI**: http://localhost:4000
- **Auth Emulator**: http://localhost:9099
- **Firestore Emulator**: http://localhost:8080
- **Storage Emulator**: http://localhost:9199
- **Functions Emulator**: http://localhost:5001

### Load Test Data

```bash
# Create test data
npm run seed

# Or manually create via UI at http://localhost:4000
```

### Reset Emulator

```bash
firebase emulators:start --import=./emulator-data --export-on-exit --force-clean
```

## Production Deployment

### 1. Build for Production

```bash
npm run build
```

Output goes to `dist/`

### 2. Deploy to Firebase Hosting

```bash
firebase deploy --only hosting
```

### 3. Deploy Cloud Functions

```bash
firebase deploy --only functions
```

### 4. Deploy Firestore Rules

```bash
firebase deploy --only firestore:rules
```

### 5. Deploy All

```bash
firebase deploy
```

## Cloud Run Deployment

### Prerequisites

- Docker installed
- Google Cloud Project configured
- Cloud Run API enabled

### 1. Create Dockerfile

```dockerfile
# See Dockerfile in root
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
COPY server.js ./
EXPOSE 8080
CMD ["node", "server.js"]
```

### 2. Build Docker Image

```bash
docker build -t admin-dashboard:latest .
```

### 3. Push to Container Registry

```bash
# Configure gcloud
gcloud config set project infinity-x-one-systems

# Push image
gcloud builds submit --tag gcr.io/infinity-x-one-systems/admin-dashboard:latest
```

### 4. Deploy to Cloud Run

```bash
gcloud run deploy admin-dashboard \
  --image gcr.io/infinity-x-one-systems/admin-dashboard:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="NODE_ENV=production"
```

### 5. Setup Custom Domain

```bash
gcloud run domain-mappings create \
  --service=admin-dashboard \
  --domain=dashboard.infinityxone.com
```

## Database Migrations

### Run Migrations

```bash
npm run db:migrate
```

### Rollback

```bash
npm run db:rollback
```

### View Migration Status

```bash
npm run db:status
```

### Create New Migration

```bash
npm run db:create-migration
```

## Monitoring & Logging

### Cloud Logging

View logs in Cloud Console:
```
https://console.cloud.google.com/logs
```

### Application Monitoring

```bash
# View real-time logs
firebase functions:log

# View Firestore usage
firebase firestore:usage
```

### Performance Monitoring

Enable in Firebase Console:
- Performance Monitoring
- Cloud Trace
- Error Reporting

### Alerts

Set up alerts in Cloud Console for:
- High error rate
- Function execution time > 30s
- Firestore quota usage > 80%
- Cloud Run memory usage > 80%

## Security Best Practices

### 1. Firestore Rules

Rules are deployed from `firebase/firestore.rules`:
- Admin: Full access
- Operator: Read all, write certain collections
- Analyst: Read all, write predictions
- Viewer: Read-only

### 2. Authentication

- Email/Password auth enabled
- Custom claims for role-based access
- Session management
- Automatic logout on inactive user

### 3. API Keys

- Use restrictive API key restrictions
- Enable only required APIs
- Rotate keys periodically
- Use environment variables (never commit keys)

### 4. CORS

Configured in `firebase.json`:
```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "headers": [{
      "source": "**",
      "headers": [{
        "key": "Cache-Control",
        "value": "max-age=3600"
      }]
    }]
  }
}
```

## Troubleshooting

### Issue: Emulator not connecting

```bash
# Check if emulator is running
lsof -i :8080  # Firestore
lsof -i :9099  # Auth
lsof -i :9199  # Storage

# Kill existing processes
kill -9 <PID>

# Restart emulator
firebase emulators:start
```

### Issue: Authentication fails

1. Check Firebase config in `.env.local`
2. Verify API Key has Auth enabled
3. Check auth rules in Firebase Console
4. Clear browser cache and cookies

### Issue: Firestore rules rejected

1. Check user role in `users` collection
2. Verify rule syntax: `firebase deploy --only firestore:rules --dry-run`
3. Check Firestore rules in Console

### Issue: Build fails

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Cloud Run deployment fails

```bash
# Check build logs
gcloud builds log <BUILD_ID>

# Check deployment
gcloud run describe admin-dashboard --region us-central1
```

## Performance Optimization

### Frontend

- Enable Code Splitting: ✓ (Vite automatic)
- Image Optimization: Use next-gen formats (WebP)
- CSS Minification: ✓ (Tailwind)
- JS Minification: ✓ (Vite)

### Backend

- Firestore Indexing: See FIRESTORE_SCHEMA.md
- Cloud Function Optimization:
  - Set memory to 512MB (2GB for heavy tasks)
  - Set timeout to 540s max
  - Use warm instances

### Caching

```bash
# Cache static assets for 1 hour
firebase.json:
{
  "hosting": {
    "headers": [{
      "source": "/**",
      "headers": [{
        "key": "Cache-Control",
        "value": "max-age=3600"
      }]
    }]
  }
}
```

## Maintenance

### Regular Tasks

- [ ] Check Cloud Run quotas weekly
- [ ] Monitor error rates daily
- [ ] Review Firestore usage monthly
- [ ] Update dependencies monthly
- [ ] Backup Firestore data weekly

### Update Dependencies

```bash
npm outdated
npm update
npm audit fix
```

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Firebase documentation: https://firebase.google.com/docs
3. Check Cloud Run documentation: https://cloud.google.com/run/docs
4. Contact the development team

---

**Last Updated**: 2024
**Version**: 1.0.0
