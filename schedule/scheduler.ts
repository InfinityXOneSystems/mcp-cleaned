/**
 * MCP-Controlled File
 * Contract: contracts/OPERATIONAL_SCHEDULE.json
 * Agent: schedule.system
 * Validator: pending
 * 
 * Operational Scheduler
 * Load OPERATIONAL_SCHEDULE.json, track due events, and log executions.
 * Events: vc-daily-crawl, vc-weekly-evolution, vc-validator-audit, vc-monthly-mutation.
 * Provide startScheduler() and stopScheduler().
 */

import fs from "fs";
import path from "path";

const SCHEDULE_PATH = path.resolve(__dirname, "../contracts/OPERATIONAL_SCHEDULE.json");
const EXECUTION_LOG_PATH = path.resolve(__dirname, "execution_log.json");

export interface ScheduledEvent {
  event_id: string;
  name: string;
  type: string;
  cron?: string;
  interval_ms?: number;
  next_run?: string;
  last_run?: string;
  enabled: boolean;
  handler?: string;
}

export interface TaskItem {
  task_id: string;
  title: string;
  description: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  status: "pending" | "in-progress" | "completed";
  due_date?: string;
  completed_at?: string;
}

export interface OperationalSchedule {
  meta: {
    version: string;
    updated: string;
    owner: string;
  };
  calendar: ScheduledEvent[];
  task_lists: Record<string, TaskItem[]>;
}

export interface ExecutionRecord {
  event_id: string;
  executed_at: string;
  status: "success" | "failed" | "skipped";
  duration_ms?: number;
  error?: string;
}

// Scheduler state
let schedulerRunning = false;
let schedulerIntervals: Map<string, NodeJS.Timeout> = new Map();
let eventHandlers: Map<string, () => Promise<void>> = new Map();

// Load schedule from disk
export function loadSchedule(): OperationalSchedule | null {
  if (!fs.existsSync(SCHEDULE_PATH)) {
    console.error(`❌ Schedule not found: ${SCHEDULE_PATH}`);
    return null;
  }
  
  try {
    const content = fs.readFileSync(SCHEDULE_PATH, "utf-8");
    return JSON.parse(content);
  } catch (error) {
    console.error(`❌ Failed to load schedule:`, error);
    return null;
  }
}

// Load execution log
function loadExecutionLog(): ExecutionRecord[] {
  if (!fs.existsSync(EXECUTION_LOG_PATH)) {
    return [];
  }
  
  try {
    const content = fs.readFileSync(EXECUTION_LOG_PATH, "utf-8");
    return JSON.parse(content);
  } catch {
    return [];
  }
}

// Save execution log
function saveExecutionLog(records: ExecutionRecord[]): void {
  fs.writeFileSync(EXECUTION_LOG_PATH, JSON.stringify(records, null, 2));
}

// Record an execution
export function recordExecution(record: ExecutionRecord): void {
  const records = loadExecutionLog();
  records.push(record);
  
  // Keep last 1000 records
  if (records.length > 1000) {
    records.splice(0, records.length - 1000);
  }
  
  saveExecutionLog(records);
  console.log(`📅 Scheduler: Recorded execution of ${record.event_id}`);
}

// Get execution history for an event
export function getExecutionHistory(eventId: string, limit: number = 10): ExecutionRecord[] {
  const records = loadExecutionLog();
  return records
    .filter(r => r.event_id === eventId)
    .slice(-limit);
}

// Register an event handler
export function registerHandler(eventId: string, handler: () => Promise<void>): void {
  eventHandlers.set(eventId, handler);
  console.log(`📅 Scheduler: Registered handler for ${eventId}`);
}

// Execute an event
async function executeEvent(event: ScheduledEvent): Promise<void> {
  const start = Date.now();
  
  console.log(`⏰ Scheduler: Executing ${event.event_id} (${event.name})`);
  
  const handler = eventHandlers.get(event.event_id);
  
  if (!handler) {
    console.warn(`⚠️  No handler registered for ${event.event_id}`);
    recordExecution({
      event_id: event.event_id,
      executed_at: new Date().toISOString(),
      status: "skipped",
      error: "No handler registered"
    });
    return;
  }
  
  try {
    await handler();
    
    recordExecution({
      event_id: event.event_id,
      executed_at: new Date().toISOString(),
      status: "success",
      duration_ms: Date.now() - start
    });
    
    console.log(`✅ Scheduler: ${event.event_id} completed in ${Date.now() - start}ms`);
  } catch (error) {
    recordExecution({
      event_id: event.event_id,
      executed_at: new Date().toISOString(),
      status: "failed",
      duration_ms: Date.now() - start,
      error: String(error)
    });
    
    console.error(`❌ Scheduler: ${event.event_id} failed:`, error);
  }
}

// Parse cron to interval (simplified - only supports basic patterns)
function cronToInterval(cron: string): number | null {
  // Simplified cron parsing
  // Format: minute hour day month weekday
  
  const parts = cron.split(" ");
  if (parts.length !== 5) return null;
  
  const [minute, hour, day, month, weekday] = parts;
  
  // Daily at specific time
  if (minute !== "*" && hour !== "*" && day === "*" && month === "*" && weekday === "*") {
    return 24 * 60 * 60 * 1000; // 24 hours
  }
  
  // Weekly
  if (weekday !== "*" && day === "*") {
    return 7 * 24 * 60 * 60 * 1000; // 7 days
  }
  
  // Monthly
  if (day !== "*" && month === "*") {
    return 30 * 24 * 60 * 60 * 1000; // 30 days
  }
  
  // Hourly
  if (minute !== "*" && hour === "*") {
    return 60 * 60 * 1000; // 1 hour
  }
  
  // Every minute
  if (minute === "*") {
    return 60 * 1000; // 1 minute
  }
  
  return null;
}

// Start the scheduler
export function startScheduler(): boolean {
  if (schedulerRunning) {
    console.warn("⚠️  Scheduler already running");
    return false;
  }
  
  const schedule = loadSchedule();
  if (!schedule) {
    console.error("❌ Failed to start scheduler: no schedule loaded");
    return false;
  }
  
  console.log("═".repeat(50));
  console.log("📅 Starting Operational Scheduler");
  console.log("═".repeat(50));
  
  for (const event of schedule.calendar) {
    if (!event.enabled) {
      console.log(`   ⏸️  ${event.event_id}: disabled`);
      continue;
    }
    
    let intervalMs = event.interval_ms;
    
    if (!intervalMs && event.cron) {
      intervalMs = cronToInterval(event.cron);
    }
    
    if (!intervalMs) {
      console.warn(`   ⚠️  ${event.event_id}: no valid interval`);
      continue;
    }
    
    // Schedule the event
    const interval = setInterval(() => {
      executeEvent(event);
    }, intervalMs);
    
    schedulerIntervals.set(event.event_id, interval);
    
    const hours = Math.round(intervalMs / (60 * 60 * 1000) * 10) / 10;
    console.log(`   ✅ ${event.event_id}: every ${hours}h`);
  }
  
  schedulerRunning = true;
  console.log("═".repeat(50));
  console.log(`📅 Scheduler started with ${schedulerIntervals.size} events`);
  
  return true;
}

// Stop the scheduler
export function stopScheduler(): void {
  if (!schedulerRunning) {
    console.warn("⚠️  Scheduler not running");
    return;
  }
  
  for (const [eventId, interval] of schedulerIntervals) {
    clearInterval(interval);
    console.log(`   ⏹️  Stopped ${eventId}`);
  }
  
  schedulerIntervals.clear();
  schedulerRunning = false;
  
  console.log("📅 Scheduler stopped");
}

// Get scheduler status
export function getSchedulerStatus(): {
  running: boolean;
  events_scheduled: number;
  registered_handlers: string[];
} {
  return {
    running: schedulerRunning,
    events_scheduled: schedulerIntervals.size,
    registered_handlers: Array.from(eventHandlers.keys())
  };
}

// Run an event immediately (manual trigger)
export async function triggerEvent(eventId: string): Promise<boolean> {
  const schedule = loadSchedule();
  if (!schedule) return false;
  
  const event = schedule.calendar.find(e => e.event_id === eventId);
  if (!event) {
    console.error(`❌ Event not found: ${eventId}`);
    return false;
  }
  
  await executeEvent(event);
  return true;
}

// Get next scheduled runs
export function getNextRuns(): { event_id: string; next_run: string }[] {
  const schedule = loadSchedule();
  if (!schedule) return [];
  
  const now = Date.now();
  const result: { event_id: string; next_run: string }[] = [];
  
  for (const event of schedule.calendar) {
    if (!event.enabled) continue;
    
    let intervalMs = event.interval_ms;
    if (!intervalMs && event.cron) {
      intervalMs = cronToInterval(event.cron);
    }
    if (!intervalMs) continue;
    
    // Calculate next run based on last execution
    const history = getExecutionHistory(event.event_id, 1);
    const lastRun = history.length > 0 
      ? new Date(history[0].executed_at).getTime()
      : now;
    
    const nextRun = new Date(lastRun + intervalMs);
    
    result.push({
      event_id: event.event_id,
      next_run: nextRun.toISOString()
    });
  }
  
  return result.sort((a, b) => 
    new Date(a.next_run).getTime() - new Date(b.next_run).getTime()
  );
}

// Export paths for testing
export { SCHEDULE_PATH, EXECUTION_LOG_PATH };
