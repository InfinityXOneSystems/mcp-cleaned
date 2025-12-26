import {
  signInWithEmailAndPassword,
  signOut,
  createUserWithEmailAndPassword,
  setPersistence,
  browserLocalPersistence,
  User,
  onAuthStateChanged,
  getAdditionalUserInfo,
} from 'firebase/auth'
import { auth, db } from '@/lib/firebase'
import { doc, getDoc, setDoc, Timestamp } from 'firebase/firestore'

export interface AuthUser {
  uid: string
  email: string | null
  displayName: string | null
  photoURL: string | null
  role: 'admin' | 'operator' | 'analyst' | 'viewer'
  permissions: string[]
}

class AuthService {
  async login(email: string, password: string): Promise<User> {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password)
      return result.user
    } catch (error: any) {
      console.error('Login error:', error)
      throw new Error(error.message)
    }
  }

  async signup(
    email: string,
    password: string,
    displayName: string,
    role: 'operator' | 'analyst' | 'viewer' = 'viewer'
  ): Promise<User> {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      const user = result.user

      // Create user document in Firestore
      await setDoc(doc(db, 'users', user.uid), {
        uid: user.uid,
        email: user.email,
        displayName,
        photoURL: user.photoURL,
        role,
        permissions: this.getPermissionsForRole(role),
        createdAt: Timestamp.now(),
        lastSignIn: Timestamp.now(),
        settings: {
          theme: 'dark',
          notifications: true,
          emailAlerts: true,
        },
      })

      return user
    } catch (error: any) {
      console.error('Signup error:', error)
      throw new Error(error.message)
    }
  }

  async logout(): Promise<void> {
    try {
      await signOut(auth)
    } catch (error) {
      console.error('Logout error:', error)
      throw error
    }
  }

  async getCurrentUser(): Promise<AuthUser | null> {
    const user = auth.currentUser
    if (!user) return null

    try {
      const userDoc = await getDoc(doc(db, 'users', user.uid))
      if (userDoc.exists()) {
        return userDoc.data() as AuthUser
      }
      return null
    } catch (error) {
      console.error('Error getting current user:', error)
      return null
    }
  }

  onAuthStateChanged(callback: (user: User | null) => void) {
    return onAuthStateChanged(auth, callback)
  }

  async getUserRole(uid: string): Promise<string | null> {
    try {
      const userDoc = await getDoc(doc(db, 'users', uid))
      return userDoc.exists() ? userDoc.data().role : null
    } catch (error) {
      console.error('Error getting user role:', error)
      return null
    }
  }

  async hasPermission(uid: string, permission: string): Promise<boolean> {
    try {
      const userDoc = await getDoc(doc(db, 'users', uid))
      if (!userDoc.exists()) return false
      return userDoc.data().permissions.includes(permission)
    } catch (error) {
      console.error('Error checking permission:', error)
      return false
    }
  }

  private getPermissionsForRole(role: string): string[] {
    const rolePermissions: Record<string, string[]> = {
      admin: [
        'manage_agents',
        'manage_users',
        'manage_properties',
        'manage_predictions',
        'view_all_data',
        'export_data',
        'manage_system',
      ],
      operator: [
        'manage_agents',
        'manage_properties',
        'create_tasks',
        'view_all_data',
        'export_data',
      ],
      analyst: [
        'view_all_data',
        'create_predictions',
        'analyze_data',
        'view_reports',
      ],
      viewer: ['view_all_data', 'view_reports'],
    }
    return rolePermissions[role] || []
  }

  async updateUserSettings(uid: string, settings: Record<string, any>) {
    try {
      const userRef = doc(db, 'users', uid)
      await setDoc(
        userRef,
        {
          settings,
          lastUpdated: Timestamp.now(),
        },
        { merge: true }
      )
    } catch (error) {
      console.error('Error updating user settings:', error)
      throw error
    }
  }
}

export const authService = new AuthService()
