import { initializeApp, getApp } from 'firebase/app'
import {
  getAuth,
  connectAuthEmulator,
  setPersistence,
  browserLocalPersistence,
} from 'firebase/auth'
import {
  getFirestore,
  connectFirestoreEmulator,
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
} from 'firebase/firestore'
import { getStorage, connectStorageEmulator } from 'firebase/storage'
import { getFunctions, connectFunctionsEmulator } from 'firebase/functions'
import { getAnalytics, isSupported } from 'firebase/analytics'

// Firebase configuration
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyDemoKeyForLocalDevelopment',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'infinity-x-one-systems.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'infinity-x-one-systems',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'infinity-x-one-systems.appspot.com',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '896380409704',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:896380409704:web:1234567890abcdef',
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
}

// Initialize Firebase app
let app
try {
  app = getApp()
} catch {
  app = initializeApp(firebaseConfig)
}

// Initialize Auth with persistence
export const auth = getAuth(app)
setPersistence(auth, browserLocalPersistence).catch((err) => {
  console.warn('Failed to set persistence:', err)
})

// Initialize Firestore with offline persistence
export const db = initializeFirestore(app, {
  localCache: persistentLocalCache({
    tabManager: persistentMultipleTabManager(),
  }),
})

// Initialize Storage
export const storage = getStorage(app)

// Initialize Functions
export const functions = getFunctions(app, 'us-central1')

// Initialize Analytics (browser only)
export let analytics: any = null
if (typeof window !== 'undefined') {
  isSupported().then((supported) => {
    if (supported) {
      analytics = getAnalytics(app)
    }
  })
}

// Connect to emulators in development
if (
  import.meta.env.DEV &&
  import.meta.env.VITE_USE_FIREBASE_EMULATORS === 'true'
) {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    // Auth Emulator
    try {
      connectAuthEmulator(auth, 'http://localhost:9099', {
        disableWarnings: true,
      })
      console.log('✓ Auth Emulator connected')
    } catch (err) {
      console.debug('Auth emulator already connected')
    }

    // Firestore Emulator
    try {
      connectFirestoreEmulator(db, 'localhost', 8080)
      console.log('✓ Firestore Emulator connected')
    } catch (err) {
      console.debug('Firestore emulator already connected')
    }

    // Storage Emulator
    try {
      connectStorageEmulator(storage, 'localhost', 9199)
      console.log('✓ Storage Emulator connected')
    } catch (err) {
      console.debug('Storage emulator already connected')
    }

    // Functions Emulator
    try {
      connectFunctionsEmulator(functions, 'localhost', 5001)
      console.log('✓ Functions Emulator connected')
    } catch (err) {
      console.debug('Functions emulator already connected')
    }
  }
}

export default app
