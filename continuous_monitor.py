#!/usr/bin/env python3
"""
INFINITY X INTELLIGENCE — CONTINUOUS MONITOR
Continuous system monitoring and autonomous operation loop
"""

import os
import time
from datetime import datetime
from typing import Dict, List

import requests

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://gateway.infinityxoneintelligence.com")
MCP_API_KEY = os.getenv("MCP_API_KEY", "INVESTORS-DEMO-KEY-2025")
LOOP_INTERVAL = int(os.getenv("LOOP_INTERVAL", "60"))  # seconds
SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() == "true"


class ContinuousMonitor:
    """Continuous monitoring and autonomous operation"""

    def __init__(self):
        self.gateway_url = GATEWAY_URL
        self.headers = {"X-MCP-KEY": MCP_API_KEY, "Content-Type": "application/json"}
        self.start_time = datetime.utcnow()
        self.cycle_count = 0
        self.metrics = {
            "health_checks": 0,
            "signals_processed": 0,
            "tasks_executed": 0,
            "anomalies_detected": 0,
            "errors": 0,
        }

    def _log(self, message: str, level: str = "INFO"):
        """Structured logging"""
        timestamp = datetime.utcnow().isoformat()
        datetime.utcnow() - self.start_time
        print(f"[{timestamp}] [Cycle {self.cycle_count}] [{level}] {message}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.gateway_url}{endpoint}"
        try:
            response = requests.request(
                method, url, headers=self.headers, timeout=10, **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {"status": "success"}
        except requests.exceptions.RequestException as e:
            self._log(f"Request failed: {endpoint} - {str(e)}", "ERROR")
            self.metrics["errors"] += 1
            return {"status": "error", "message": str(e)}

    # ═══════════════════════════════════════════════════════
    # MONITORING TASKS
    # ═══════════════════════════════════════════════════════

    def check_system_health(self) -> bool:
        """Check all system health endpoints"""
        endpoints = ["/health", "/autonomy/health", "/langchain/health"]

        all_healthy = True
        for endpoint in endpoints:
            result = self._make_request("GET", endpoint)
            if result.get("status") != "success":
                self._log(f"⚠️ Health check failed: {endpoint}", "WARN")
                all_healthy = False

        self.metrics["health_checks"] += 1
        return all_healthy

    def process_new_signals(self) -> int:
        """Process new signals from memory"""
        # Query for unprocessed signals
        signals = self._make_request(
            "GET", "/memory/query", params={"type": "signal", "limit": 50}
        )

        if not signals or "data" not in signals:
            return 0

        entries = signals.get("data", {}).get("entries", [])
        processed = 0

        for signal in entries:
            # Check if signal requires action
            confidence = signal.get("confidence", 0.0)
            if confidence >= 0.8:
                self._log(f"🎯 High-confidence signal detected: {signal.get('type')}")
                # Process signal (implementation specific)
                processed += 1

        self.metrics["signals_processed"] += processed
        return processed

    def execute_pending_tasks(self) -> int:
        """Execute pending agent tasks"""
        # Query for pending tasks
        tasks = self._make_request(
            "GET",
            "/v1/intelligence/memory",
            params={"type": "task", "status": "pending"},
        )

        if not tasks or "data" not in tasks:
            return 0

        pending = tasks.get("data", {}).get("tasks", [])
        executed = 0

        for task in pending[:5]:  # Limit to 5 per cycle
            task_id = task.get("id")
            self._log(f"▶️ Executing task: {task_id}")

            # Execute via MCP
            result = self._make_request(
                "POST",
                "/mcp/execute",
                json={
                    "tool_name": task.get("tool_name"),
                    "arguments": task.get("arguments", {}),
                    "execution_mode": "LIVE" if not SAFE_MODE else "DRY_RUN",
                },
            )

            if result.get("status") == "success":
                executed += 1

        self.metrics["tasks_executed"] += executed
        return executed

    def detect_anomalies(self) -> List[Dict]:
        """Detect system anomalies"""
        anomalies = []

        # Check error rate
        if self.metrics["errors"] > 10:
            anomalies.append(
                {
                    "type": "high_error_rate",
                    "severity": "high",
                    "message": f"Error count: {self.metrics['errors']}",
                }
            )

        # Check agent health
        agents = self._make_request("GET", "/agents/list")
        if agents and "data" in agents:
            for agent in agents["data"].get("agents", []):
                if agent.get("status") == "error":
                    anomalies.append(
                        {
                            "type": "agent_failure",
                            "severity": "medium",
                            "message": f"Agent {agent.get('name')} in error state",
                        }
                    )

        self.metrics["anomalies_detected"] += len(anomalies)
        return anomalies

    def update_metrics(self):
        """Update and persist system metrics"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        metrics_snapshot = {
            "type": "system",
            "content": {
                "event": "metrics_update",
                "cycle": self.cycle_count,
                "uptime_seconds": uptime,
                "metrics": self.metrics,
            },
            "confidence": 1.0,
            "sources": ["continuous_monitor"],
        }

        self._make_request("POST", "/memory/write", json=metrics_snapshot)

    def persist_state(self):
        """Persist current system state"""
        state = {
            "type": "system",
            "content": {
                "event": "state_snapshot",
                "cycle": self.cycle_count,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": self.metrics,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            },
            "confidence": 1.0,
            "sources": ["continuous_monitor"],
        }

        self._make_request("POST", "/memory/write", json=state)

    # ═══════════════════════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════════════════════

    def run_cycle(self):
        """Execute one monitoring cycle"""
        self.cycle_count += 1

        self._log(f"═══ Cycle {self.cycle_count} Start ═══")

        # Task 1: Health checks
        healthy = self.check_system_health()
        if healthy:
            self._log("✅ System health: OK")
        else:
            self._log("⚠️ System health: DEGRADED", "WARN")

        # Task 2: Process signals
        signals = self.process_new_signals()
        if signals > 0:
            self._log(f"📡 Processed {signals} signals")

        # Task 3: Execute tasks
        tasks = self.execute_pending_tasks()
        if tasks > 0:
            self._log(f"⚙️ Executed {tasks} tasks")

        # Task 4: Detect anomalies
        anomalies = self.detect_anomalies()
        if anomalies:
            self._log(f"🚨 Detected {len(anomalies)} anomalies", "WARN")
            for anomaly in anomalies:
                self._log(f"   - {anomaly['type']}: {anomaly['message']}", "WARN")

        # Task 5: Update metrics
        self.update_metrics()

        # Task 6: Persist state (every 10 cycles)
        if self.cycle_count % 10 == 0:
            self.persist_state()
            self._log(f"💾 State persisted (cycle {self.cycle_count})")

        self._log(f"═══ Cycle {self.cycle_count} Complete ═══")
        self._log("")

    def run(self):
        """Main continuous loop"""
        self._log("╔══════════════════════════════════════════════════════════╗")
        self._log("║      INFINITY X INTELLIGENCE — CONTINUOUS MONITOR        ║")
        self._log("╚══════════════════════════════════════════════════════════╝")
        self._log("")
        self._log(f"Gateway: {self.gateway_url}")
        self._log(f"Loop Interval: {LOOP_INTERVAL}s")
        self._log(f"Safe Mode: {SAFE_MODE}")
        self._log(f"Start Time: {self.start_time.isoformat()}")
        self._log("")
        self._log("🚀 Continuous monitoring active...")
        self._log("")

        try:
            while True:
                self.run_cycle()
                time.sleep(LOOP_INTERVAL)
        except KeyboardInterrupt:
            self._log("", "INFO")
            self._log("⏹️ Shutdown signal received", "INFO")
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        self._log("Persisting final state...")
        self.persist_state()

        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        self._log("")
        self._log("╔══════════════════════════════════════════════════════════╗")
        self._log("║                  MONITOR SHUTDOWN                        ║")
        self._log("╚══════════════════════════════════════════════════════════╝")
        self._log(f"Total Cycles: {self.cycle_count}")
        self._log(f"Uptime: {uptime:.0f}s ({uptime/3600:.1f}h)")
        self._log(f"Health Checks: {self.metrics['health_checks']}")
        self._log(f"Signals Processed: {self.metrics['signals_processed']}")
        self._log(f"Tasks Executed: {self.metrics['tasks_executed']}")
        self._log(f"Anomalies Detected: {self.metrics['anomalies_detected']}")
        self._log(f"Errors: {self.metrics['errors']}")
        self._log("")
        self._log("✨ Monitor shutdown complete")


def main():
    """Main entry point"""
    monitor = ContinuousMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
