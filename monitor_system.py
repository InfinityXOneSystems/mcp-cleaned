#!/usr/bin/env python3
"""
Comprehensive System Health Monitor
Monitors all infrastructure and sends alerts
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict

import requests


class SystemMonitor:
    def __init__(self):
        self.project = os.getenv("GCP_PROJECT_ID", "infinity-x-one-systems")
        self.region = os.getenv("GCP_REGION", "us-central1")
        self.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8000")
        self.checks = {}
        self.alerts = []
        self.timestamp = datetime.now().isoformat()

    def check_cloud_run(self) -> Dict[str, Any]:
        """Check Cloud Run service status"""
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "run",
                    "services",
                    "describe",
                    "gateway",
                    "--project",
                    self.project,
                    "--region",
                    self.region,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                status = {
                    "service": "gateway",
                    "status": "RUNNING",
                    "url": data.get("status", {}).get("url", "N/A"),
                    "region": self.region,
                    "traffic": data.get("spec", {}).get("traffic", []),
                }
                return status
            else:
                self.alerts.append("Cloud Run service check failed")
                return {"status": "ERROR", "error": result.stderr}
        except Exception as e:
            self.alerts.append(f"Cloud Run check error: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def check_api_health(self) -> Dict[str, Any]:
        """Check API endpoint health"""
        endpoints = {
            "health": "/health",
            "dashboard": "/dashboard",
            "openapi": "/openapi/combined.yaml",
            "api_docs": "/docs",
        }

        results = {}
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.gateway_url}{endpoint}", timeout=5)
                results[name] = {
                    "status_code": response.status_code,
                    "ok": response.status_code < 400,
                    "response_time": response.elapsed.total_seconds(),
                }
                if response.status_code >= 400:
                    self.alerts.append(
                        f"{name} endpoint returned {response.status_code}"
                    )
            except requests.exceptions.Timeout:
                results[name] = {"status": "TIMEOUT"}
                self.alerts.append(f"{name} endpoint timed out")
            except requests.exceptions.ConnectionError:
                results[name] = {"status": "CONNECTION_ERROR"}
                self.alerts.append(f"Cannot connect to {name} endpoint")
            except Exception as e:
                results[name] = {"status": "ERROR", "error": str(e)}
                self.alerts.append(f"{name} check error: {str(e)}")

        return results

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            import sqlite3

            conn = sqlite3.connect("mcp_memory.db")
            cursor = conn.cursor()

            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            count = cursor.fetchone()[0]

            conn.close()
            return {
                "status": "CONNECTED",
                "type": "SQLite",
                "file": "mcp_memory.db",
                "tables": count,
            }
        except FileNotFoundError:
            return {"status": "DATABASE_FILE_NOT_FOUND"}
        except Exception as e:
            self.alerts.append(f"Database error: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def check_git_status(self) -> Dict[str, Any]:
        """Check git repository status"""
        try:
            # Get latest commit
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%ai|%s"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                commit_hash, commit_time, commit_msg = result.stdout.strip().split("|")

                # Check if there are uncommitted changes
                result2 = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                has_changes = len(result2.stdout.strip()) > 0

                return {
                    "latest_commit": commit_hash[:7],
                    "commit_time": commit_time,
                    "commit_message": commit_msg[:60],
                    "uncommitted_changes": has_changes,
                    "changes_count": (
                        len(result2.stdout.strip().split("\n")) if has_changes else 0
                    ),
                }
            return {"status": "ERROR"}
        except Exception as e:
            self.alerts.append(f"Git check error: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def check_builds(self) -> Dict[str, Any]:
        """Check recent Cloud Build status"""
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "builds",
                    "list",
                    "--project",
                    self.project,
                    "--limit",
                    "5",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                builds = json.loads(result.stdout)
                if builds:
                    latest = builds[0]
                    status = latest.get("status", "UNKNOWN")

                    if status == "FAILURE":
                        self.alerts.append(
                            f'Build {latest.get("id", "unknown")} FAILED'
                        )

                    return {
                        "latest_build_id": latest.get("id"),
                        "latest_build_status": status,
                        "create_time": latest.get("createTime"),
                        "total_recent": len(builds),
                    }
            return {"status": "NO_BUILDS"}
        except Exception as e:
            self.alerts.append(f"Build check error: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def generate_report(self) -> Dict[str, Any]:
        """Generate complete health report"""
        self.checks = {
            "timestamp": self.timestamp,
            "project": self.project,
            "cloud_run": self.check_cloud_run(),
            "api_health": self.check_api_health(),
            "database": self.check_database(),
            "git": self.check_git_status(),
            "builds": self.check_builds(),
            "alerts": self.alerts,
            "alert_count": len(self.alerts),
            "overall_status": (
                "HEALTHY"
                if not self.alerts
                else "DEGRADED" if len(self.alerts) < 3 else "CRITICAL"
            ),
        }
        return self.checks

    def print_report(self):
        """Print formatted report"""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("SYSTEM HEALTH REPORT")
        print("=" * 80)
        print(f"Time: {report['timestamp']}")
        print(f"Project: {report['project']}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Alerts: {report['alert_count']}")

        print("\n--- Cloud Run ---")
        for k, v in report["cloud_run"].items():
            print(f"  {k}: {v}")

        print("\n--- API Health ---")
        for endpoint, health in report["api_health"].items():
            status = "✓" if health.get("ok") else "✗"
            print(f"  {status} {endpoint}: {health}")

        print("\n--- Database ---")
        for k, v in report["database"].items():
            print(f"  {k}: {v}")

        print("\n--- Git ---")
        for k, v in report["git"].items():
            print(f"  {k}: {v}")

        print("\n--- Builds ---")
        for k, v in report["builds"].items():
            print(f"  {k}: {v}")

        if report["alerts"]:
            print("\n--- ALERTS ---")
            for alert in report["alerts"]:
                print(f"  ⚠️  {alert}")

        print("=" * 80 + "\n")

        # Return JSON for CI/CD
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.print_report()

    # Exit with error code if critical
    sys.exit(2 if len(monitor.alerts) > 2 else 1 if monitor.alerts else 0)
