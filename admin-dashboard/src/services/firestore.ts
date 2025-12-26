import {
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  updateDoc,
  deleteDoc,
  Timestamp,
  QueryConstraint,
  QueryFieldFilterConstraint,
} from 'firebase/firestore'
import { db } from '@/lib/firebase'
import type { Agent, AgentTask, RealEstateProperty, LoanSignal, Prediction, ChatMessage } from '@/types'

/**
 * Generic Firestore operations
 */
export const firestoreService = {
  async getDoc<T>(collectionName: string, docId: string): Promise<T | null> {
    const docRef = doc(db, collectionName, docId)
    const snapshot = await getDoc(docRef)
    return snapshot.exists() ? { ...snapshot.data(), id: snapshot.id } as T : null
  },

  async getAllDocs<T>(collectionName: string, constraints: QueryConstraint[] = []): Promise<T[]> {
    const q = query(collection(db, collectionName), ...constraints)
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => ({ ...doc.data(), id: doc.id } as T))
  },

  async setDoc<T extends { id?: string }>(collectionName: string, docId: string, data: T, merge = false) {
    const docRef = doc(db, collectionName, docId)
    await setDoc(docRef, data, { merge })
  },

  async updateDoc(collectionName: string, docId: string, data: Record<string, any>) {
    const docRef = doc(db, collectionName, docId)
    await updateDoc(docRef, data)
  },

  async deleteDoc(collectionName: string, docId: string) {
    const docRef = doc(db, collectionName, docId)
    await deleteDoc(docRef)
  },

  subscribe<T>(collectionName: string, constraints: QueryConstraint[], callback: (data: T[]) => void) {
    const q = query(collection(db, collectionName), ...constraints)
    return onSnapshot(q, snapshot => {
      const data = snapshot.docs.map(doc => ({ ...doc.data(), id: doc.id } as T))
      callback(data)
    })
  },
}

/**
 * Agent Service - Firestore operations for agents
 */
export const agentService = {
  async getAllAgents(): Promise<Agent[]> {
    return firestoreService.getAllDocs<Agent>('agents', [orderBy('name')])
  },

  async getAgent(agentId: string): Promise<Agent | null> {
    return firestoreService.getDoc<Agent>('agents', agentId)
  },

  async getActiveAgents(): Promise<Agent[]> {
    return firestoreService.getAllDocs<Agent>('agents', [
      where('status', '==', 'active') as QueryFieldFilterConstraint,
      orderBy('lastRun', 'desc'),
    ])
  },

  subscribeToAgent(agentId: string, callback: (agent: Agent) => void) {
    return onSnapshot(doc(db, 'agents', agentId), snapshot => {
      if (snapshot.exists()) {
        callback({ ...snapshot.data(), id: snapshot.id } as Agent)
      }
    })
  },

  subscribeToAgents(callback: (agents: Agent[]) => void) {
    return firestoreService.subscribe<Agent>(
      'agents',
      [orderBy('updatedAt', 'desc')],
      callback
    )
  },

  async updateAgent(agentId: string, updates: Partial<Agent>) {
    await firestoreService.updateDoc('agents', agentId, {
      ...updates,
      updatedAt: Timestamp.now(),
    })
  },

  async createAgent(agent: Omit<Agent, 'id'>): Promise<string> {
    const docRef = doc(collection(db, 'agents'))
    await firestoreService.setDoc('agents', docRef.id, {
      ...agent,
      id: docRef.id,
      createdAt: Timestamp.now(),
      updatedAt: Timestamp.now(),
    })
    return docRef.id
  },

  async deleteAgent(agentId: string) {
    await firestoreService.deleteDoc('agents', agentId)
  },

  async startAgentTask(agentId: string, taskType: string) {
    const docRef = doc(collection(db, 'agent_tasks'))
    const task: AgentTask = {
      id: docRef.id,
      agentId,
      taskType,
      status: 'pending',
      startedAt: new Date(),
    }
    await firestoreService.setDoc('agent_tasks', docRef.id, task)
    return docRef.id
  },

  async getAgentTasks(agentId: string, limitCount: number = 50) {
    return firestoreService.getAllDocs<AgentTask>('agent_tasks', [
      where('agentId', '==', agentId) as QueryFieldFilterConstraint,
      orderBy('startedAt', 'desc'),
      limit(limitCount),
    ])
  },

  subscribeToAgentTasks(agentId: string, callback: (tasks: AgentTask[]) => void) {
    return firestoreService.subscribe<AgentTask>(
      'agent_tasks',
      [
        where('agentId', '==', agentId) as QueryFieldFilterConstraint,
        orderBy('startedAt', 'desc'),
        limit(100),
      ],
      callback
    )
  },

  async updateTask(taskId: string, updates: Partial<AgentTask>) {
    await firestoreService.updateDoc('agent_tasks', taskId, updates)
  },
}

/**
 * Real Estate Service
 */
export const realEstateService = {
  async getProperties(limitCount: number = 100): Promise<RealEstateProperty[]> {
    return firestoreService.getAllDocs<RealEstateProperty>('properties', [
      orderBy('updatedAt', 'desc'),
      limit(limitCount),
    ])
  },

  async getPropertyById(propertyId: string): Promise<RealEstateProperty | null> {
    return firestoreService.getDoc<RealEstateProperty>('properties', propertyId)
  },

  async getPropertiesByCity(city: string): Promise<RealEstateProperty[]> {
    return firestoreService.getAllDocs<RealEstateProperty>('properties', [
      where('city', '==', city) as QueryFieldFilterConstraint,
      orderBy('distressScore', 'desc'),
    ])
  },

  subscribeToProperties(callback: (props: RealEstateProperty[]) => void) {
    return firestoreService.subscribe<RealEstateProperty>(
      'properties',
      [orderBy('distressScore', 'desc'), limit(50)],
      callback
    )
  },

  async addProperty(property: Omit<RealEstateProperty, 'id'>) {
    const docRef = doc(collection(db, 'properties'))
    await firestoreService.setDoc('properties', docRef.id, {
      ...property,
      id: docRef.id,
      discoveredAt: Timestamp.now(),
      lastUpdated: Timestamp.now(),
    })
    return docRef.id
  },

  async updateProperty(propertyId: string, updates: Partial<RealEstateProperty>) {
    await firestoreService.updateDoc('properties', propertyId, {
      ...updates,
      lastUpdated: Timestamp.now(),
    })
  },

  async deleteProperty(propertyId: string) {
    await firestoreService.deleteDoc('properties', propertyId)
  },
}

/**
 * Loan Signal Service
 */
export const loanSignalService = {
  async getSignals(limitCount: number = 100): Promise<LoanSignal[]> {
    return firestoreService.getAllDocs<LoanSignal>('loan_signals', [
      orderBy('urgencyScore', 'desc'),
      limit(limitCount),
    ])
  },

  async getUnprocessedSignals(): Promise<LoanSignal[]> {
    return firestoreService.getAllDocs<LoanSignal>('loan_signals', [
      where('processed', '==', false) as QueryFieldFilterConstraint,
      orderBy('createdAt', 'desc'),
    ])
  },

  subscribeToSignals(callback: (signals: LoanSignal[]) => void) {
    return firestoreService.subscribe<LoanSignal>(
      'loan_signals',
      [orderBy('urgencyScore', 'desc'), limit(100)],
      callback
    )
  },

  async addSignal(signal: Omit<LoanSignal, 'id'>) {
    const docRef = doc(collection(db, 'loan_signals'))
    await firestoreService.setDoc('loan_signals', docRef.id, {
      ...signal,
      id: docRef.id,
      discoveredAt: Timestamp.now(),
    })
    return docRef.id
  },

  async updateSignal(signalId: string, updates: Partial<LoanSignal>) {
    await firestoreService.updateDoc('loan_signals', signalId, updates)
  },

  async markProcessed(signalId: string) {
    await firestoreService.updateDoc('loan_signals', signalId, { processed: true })
  },
}

/**
 * Prediction Service
 */
export const predictionService = {
  async getPredictions(limitCount: number = 100): Promise<Prediction[]> {
    return firestoreService.getAllDocs<Prediction>('predictions', [
      orderBy('createdAt', 'desc'),
      limit(limitCount),
    ])
  },

  async getPredictionsForProperty(propertyId: string): Promise<Prediction[]> {
    return firestoreService.getAllDocs<Prediction>('predictions', [
      where('propertyId', '==', propertyId) as QueryFieldFilterConstraint,
      orderBy('createdAt', 'desc'),
    ])
  },

  async createPrediction(prediction: Omit<Prediction, 'id'>) {
    const docRef = doc(collection(db, 'predictions'))
    await firestoreService.setDoc('predictions', docRef.id, {
      ...prediction,
      id: docRef.id,
      createdAt: Timestamp.now(),
      updatedAt: Timestamp.now(),
    })
    return docRef.id
  },

  async updatePrediction(predictionId: string, updates: Partial<Prediction>) {
    await firestoreService.updateDoc('predictions', predictionId, {
      ...updates,
      updatedAt: Timestamp.now(),
    })
  },
}

/**
 * Chat Service
 */
export const chatService = {
  async getMessages(limitCount: number = 50): Promise<ChatMessage[]> {
    return firestoreService.getAllDocs<ChatMessage>('chat', [
      orderBy('createdAt', 'desc'),
      limit(limitCount),
    ])
  },

  async createMessage(message: Omit<ChatMessage, 'id' | 'createdAt'>) {
    const docRef = doc(collection(db, 'chat'))
    await firestoreService.setDoc('chat', docRef.id, {
      ...message,
      id: docRef.id,
      createdAt: Timestamp.now(),
    })
    return docRef.id
  },

  subscribeToMessages(callback: (messages: ChatMessage[]) => void) {
    return firestoreService.subscribe<ChatMessage>(
      'chat',
      [orderBy('createdAt', 'desc'), limit(100)],
      callback
    )
  },
}

/**
 * Notification Service
 */
export const notificationService = {
  async getUserNotifications(userId: string, limitCount: number = 50) {
    return firestoreService.getAllDocs<any>('notifications', [
      where('userId', '==', userId) as QueryFieldFilterConstraint,
      orderBy('createdAt', 'desc'),
      limit(limitCount),
    ])
  },

  subscribeToNotifications(userId: string, callback: (notifications: any[]) => void) {
    return firestoreService.subscribe<any>(
      'notifications',
      [
        where('userId', '==', userId) as QueryFieldFilterConstraint,
        orderBy('createdAt', 'desc'),
        limit(100),
      ],
      callback
    )
  },

  async markAsRead(notificationId: string) {
    await firestoreService.updateDoc('notifications', notificationId, { read: true })
  },

  async createNotification(notification: any) {
    const docRef = doc(collection(db, 'notifications'))
    await firestoreService.setDoc('notifications', docRef.id, {
      ...notification,
      createdAt: Timestamp.now(),
    })
    return docRef.id
  },
}
