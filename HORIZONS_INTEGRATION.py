"""
Horizons React - Google Cloud Backend Integration
Frontend integration code for Horizons React SPA
Connects to Infinity XOS API Gateway + Cloud Run services
"""

# ===== HORIZONS REACT INTEGRATION GUIDE =====
# 
# This file documents how to integrate your Horizons React frontend
# with the Infinity XOS backend (Google Cloud Run + Firestore)
#
# =======================================================

# 1. ENVIRONMENT CONFIGURATION
# =======================================================

# In your Horizons React .env file:
"""
REACT_APP_API_GATEWAY=http://localhost:8000  # Local development
# OR for Cloud Run:
# REACT_APP_API_GATEWAY=https://api-gateway-896380409704.us-east1.run.app

REACT_APP_FIREBASE_API_KEY=AIzaSyDu...
REACT_APP_FIREBASE_AUTH_DOMAIN=infinity-x-one-systems.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=infinity-x-one-systems
REACT_APP_FIREBASE_STORAGE_BUCKET=infinity-x-one-systems.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=896380409704
REACT_APP_FIREBASE_APP_ID=1:896380409704:web:abc...

REACT_APP_ENABLE_AUTH=true  # Set false for DEV mode (no auth)
"""

# 2. FIREBASE AUTHENTICATION SERVICE
# =======================================================

"""
// horizons/src/services/firebaseAuth.ts

import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

export const loginUser = async (email: string, password: string) => {
  return await signInWithEmailAndPassword(auth, email, password);
};

export const registerUser = async (email: string, password: string) => {
  return await createUserWithEmailAndPassword(auth, email, password);
};

export const logoutUser = async () => {
  return await signOut(auth);
};

export const getAuthToken = async () => {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  return null;
};
"""

# 3. API CLIENT SERVICE
# =======================================================

"""
// horizons/src/services/apiClient.ts

import axios, { AxiosInstance } from 'axios';
import { getAuthToken } from './firebaseAuth';

class InfinityXOSClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_GATEWAY || 'http://localhost:8000';
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
    });

    // Add auth interceptor
    this.client.interceptors.request.use(async (config) => {
      const token = await getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // ===== UNIFIED ENDPOINTS =====

  async predict(params: {
    asset: string;
    asset_type?: string;
    prediction_type?: string;
    timeframe?: string;
    confidence?: number;
  }) {
    return this.client.post('/predict', params);
  }

  async crawl(params: {
    url: string;
    depth?: number;
    max_pages?: number;
    filters?: Record<string, any>;
  }) {
    return this.client.post('/crawl', params);
  }

  async simulate(params: {
    scenario: string;
    asset?: string;
    parameters?: Record<string, any>;
  }) {
    return this.client.post('/simulate', params);
  }

  // ===== READ/WRITE/ANALYZE OPERATIONS =====

  async read(resource: string, options?: Record<string, any>) {
    return this.client.post(`/read/${resource}`, options || {});
  }

  async write(resource: string, data: Record<string, any>) {
    return this.client.post(`/write/${resource}`, data);
  }

  async analyze(resource: string, options?: Record<string, any>) {
    return this.client.post(`/analyze/${resource}`, options || {});
  }

  // ===== PORTFOLIO ENDPOINTS =====

  async getPortfolio() {
    return this.client.get('/api/portfolio');
  }

  async getBankBalance() {
    return this.client.get('/api/bank');
  }

  async depositFunds(amount: number) {
    return this.client.post('/api/bank/deposit', { amount });
  }

  async addPosition(asset: string, direction: string, price: number, quantity: number) {
    return this.client.post('/api/portfolio/add-position', {
      asset,
      direction,
      price,
      quantity,
    });
  }

  // ===== INTELLIGENCE ENDPOINTS =====

  async getIntelligenceCategories() {
    return this.client.get('/api/intelligence/categories');
  }

  async getIntelligenceSources(category?: string, subcategory?: string) {
    return this.client.get('/api/intelligence/sources', {
      params: { category, subcategory },
    });
  }

  async previewIntelligenceSource(sourceId: number) {
    return this.client.get(`/api/intelligence/preview/${sourceId}`);
  }

  // ===== COMPLIANCE & AUDIT =====

  async getComplianceStatus() {
    return this.client.get('/compliance/status');
  }

  async getComplianceAuditLog(limit: number = 100) {
    return this.client.get('/compliance/audit-log', {
      params: { limit },
    });
  }

  // ===== HEALTH & MONITORING =====

  async health() {
    return this.client.get('/health');
  }
}

export const apiClient = new InfinityXOSClient();
"""

# 4. REACT HOOKS FOR API CALLS
# =======================================================

"""
// horizons/src/hooks/useInfinityXOS.ts

import { useState, useCallback } from 'react';
import { apiClient } from '../services/apiClient';
import { useAuth } from './useAuth';

export function usePrediction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const predict = useCallback(async (params: {
    asset: string;
    asset_type?: string;
    prediction_type?: string;
    timeframe?: string;
    confidence?: number;
  }) => {
    if (!isAuthenticated) {
      setError('Not authenticated');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.predict(params);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  return { predict, loading, error };
}

export function useCrawl() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const crawl = useCallback(async (params: {
    url: string;
    depth?: number;
    max_pages?: number;
  }) => {
    if (!isAuthenticated) {
      setError('Not authenticated');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.crawl(params);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  return { crawl, loading, error };
}

export function useSimulate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const simulate = useCallback(async (params: {
    scenario: string;
    asset?: string;
    parameters?: Record<string, any>;
  }) => {
    if (!isAuthenticated) {
      setError('Not authenticated');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.simulate(params);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  return { simulate, loading, error };
}

export function usePortfolio() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const getPortfolio = useCallback(async () => {
    if (!isAuthenticated) {
      setError('Not authenticated');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getPortfolio();
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const addPosition = useCallback(async (asset: string, direction: string, price: number, quantity: number) => {
    if (!isAuthenticated) {
      setError('Not authenticated');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.addPosition(asset, direction, price, quantity);
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  return { getPortfolio, addPosition, loading, error };
}
"""

# 5. COMPONENT EXAMPLE - PREDICT TOOL
# =======================================================

"""
// horizons/src/components/PredictTool.tsx

import React, { useState } from 'react';
import { usePrediction } from '../hooks/useInfinityXOS';
import { useAuth } from '../hooks/useAuth';

export const PredictTool: React.FC = () => {
  const { user } = useAuth();
  const { predict, loading, error } = usePrediction();

  const [asset, setAsset] = useState('BTC');
  const [timeframe, setTimeframe] = useState('24h');
  const [confidence, setConfidence] = useState(50);
  const [result, setResult] = useState<any>(null);

  const handlePredict = async () => {
    const result = await predict({
      asset,
      asset_type: 'crypto',
      prediction_type: 'price',
      timeframe,
      confidence,
    });

    if (result) {
      setResult(result);
    }
  };

  if (!user) {
    return <div>Please log in to use prediction tools.</div>;
  }

  return (
    <div className="predict-tool">
      <h2>🔮 Asset Prediction</h2>

      <div className="form-group">
        <label>Asset Symbol</label>
        <input
          type="text"
          value={asset}
          onChange={(e) => setAsset(e.target.value.toUpperCase())}
          placeholder="BTC, TSLA, SPY..."
        />
      </div>

      <div className="form-group">
        <label>Timeframe</label>
        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
          <option>1h</option>
          <option>4h</option>
          <option>24h</option>
          <option>7d</option>
          <option>30d</option>
        </select>
      </div>

      <div className="form-group">
        <label>Confidence Level: {confidence}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={confidence}
          onChange={(e) => setConfidence(parseInt(e.target.value))}
        />
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
      >
        {loading ? 'Predicting...' : '🚀 Generate Prediction'}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result">
          <h3>Prediction Result</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
"""

# 6. DEPLOYMENT CHECKLIST
# =======================================================

DEPLOYMENT_CHECKLIST = """
HORIZONS REACT + INFINITY XOS INTEGRATION CHECKLIST
====================================================

Local Development:
  ☐ Install dependencies: npm install axios firebase
  ☐ Copy .env.example to .env and fill in Firebase credentials
  ☐ Start Infinity XOS local services:
    - python dashboard_api.py (port 8001)
    - python intelligence_api.py (port 8002)
    - python meta_service.py (port 8003)
    - python api_gateway.py (port 8000)
  ☐ Start Horizons: npm start
  ☐ Test login with Firebase Auth
  ☐ Test /predict, /crawl, /simulate endpoints

Cloud Deployment:
  ☐ Build Horizons: npm run build
  ☐ Deploy API Gateway to Cloud Run
  ☐ Deploy Dashboard API to Cloud Run
  ☐ Deploy Intelligence API to Cloud Run
  ☐ Deploy Meta Service to Cloud Run
  ☐ Configure Firestore rules for auth
  ☐ Update REACT_APP_API_GATEWAY to Cloud Run URL
  ☐ Enable CORS on all backends
  ☐ Test end-to-end: Horizons → Cloud Gateway → Services

Compliance:
  ☐ Verify compliance layer is active (/compliance/status)
  ☐ Check rate limits are enforced
  ☐ Review audit log for violations
  ☐ Test Google/GitHub/OpenAI mandatory requirements
  ☐ Enable HTTPS on all endpoints

Security:
  ☐ Firebase Auth enabled and configured
  ☐ API keys in environment variables only
  ☐ CORS properly configured
  ☐ Rate limiting active
  ☐ Audit logging enabled
"""

# 7. TESTING THE UNIFIED ENDPOINTS
# =======================================================

TESTING_GUIDE = """
TESTING UNIFIED ENDPOINTS
===========================

Test /predict:
  curl -X POST http://localhost:8000/predict \\
    -H "Content-Type: application/json" \\
    -H "Authorization: Bearer YOUR_TOKEN" \\
    -d '{
      "asset": "BTC",
      "asset_type": "crypto",
      "prediction_type": "price",
      "timeframe": "24h",
      "confidence": 75
    }'

Test /crawl:
  curl -X POST http://localhost:8000/crawl \\
    -H "Content-Type: application/json" \\
    -H "Authorization: Bearer YOUR_TOKEN" \\
    -d '{
      "url": "https://example.com",
      "depth": 2,
      "max_pages": 50
    }'

Test /simulate:
  curl -X POST http://localhost:8000/simulate \\
    -H "Content-Type: application/json" \\
    -H "Authorization: Bearer YOUR_TOKEN" \\
    -d '{
      "scenario": "backtest",
      "asset": "BTC",
      "parameters": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
      }
    }'

Test Compliance:
  curl http://localhost:8000/compliance/status
  curl http://localhost:8000/compliance/audit-log?limit=50

Test Gateway Health:
  curl http://localhost:8000/health
"""

print("✓ Horizons React Integration guide created")
print("\nTo use:")
print("  1. Copy the Firebase auth service to your Horizons project")
print("  2. Copy the API client service")
print("  3. Copy the React hooks")
print("  4. Use hooks in your components")
print("  5. See DEPLOYMENT_CHECKLIST for full setup")
