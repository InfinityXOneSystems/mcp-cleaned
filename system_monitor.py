#!/usr/bin/env python3
"""
Infinity XOS - System Status Monitor
Real-time monitoring of all services and compliance status
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any
import json

class SystemMonitor:
    """Monitor all Infinity XOS services"""
    
    SERVICES = {
        "gateway": "http://localhost:8000",
        "dashboard": "http://localhost:8001",
        "intelligence": "http://localhost:8002",
        "meta": "http://localhost:8003",
    }
    
    async def check_service(self, name: str, url: str) -> Dict[str, Any]:
        """Check if service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    return {
                        "status": "🟢 ONLINE",
                        "response_time": f"{response.elapsed.total_seconds():.2f}s",
                        "data": response.json()
                    }
                else:
                    return {
                        "status": "🔴 ERROR",
                        "code": response.status_code,
                        "message": response.text[:100]
                    }
        except Exception as e:
            return {
                "status": "🔴 OFFLINE",
                "error": str(e)
            }
    
    async def check_compliance(self) -> Dict[str, Any]:
        """Check compliance status"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get("http://localhost:8000/compliance/status")
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": "Compliance check failed", "code": response.status_code}
        except Exception as e:
            return {"error": f"Compliance check failed: {e}"}
    
    async def check_database(self) -> Dict[str, Any]:
        """Check SQLite database status"""
        try:
            import sqlite3
            conn = sqlite3.connect('mcp_memory.db')
            cur = conn.cursor()
            
            # Get table counts
            tables = {}
            for table in ['memory', 'predictions', 'jobs', 'paper_accounts', 'paper_positions']:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    tables[table] = count
                except:
                    tables[table] = "ERROR"
            
            conn.close()
            
            return {
                "status": "🟢 ONLINE",
                "database": "mcp_memory.db",
                "tables": tables
            }
        except Exception as e:
            return {
                "status": "🔴 OFFLINE",
                "error": str(e)
            }
    
    async def test_endpoints(self) -> Dict[str, Any]:
        """Test key endpoints"""
        results = {}
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Test /predict
            try:
                response = await client.post(
                    "http://localhost:8000/predict",
                    json={"asset": "BTC", "timeframe": "24h"},
                    timeout=5
                )
                results["predict"] = "✅ PASS" if response.status_code == 200 else f"❌ {response.status_code}"
            except Exception as e:
                results["predict"] = f"❌ {str(e)[:30]}"
            
            # Test /crawl
            try:
                response = await client.post(
                    "http://localhost:8000/crawl",
                    json={"url": "https://example.com"},
                    timeout=5
                )
                results["crawl"] = "✅ PASS" if response.status_code == 200 else f"❌ {response.status_code}"
            except Exception as e:
                results["crawl"] = f"❌ {str(e)[:30]}"
            
            # Test /simulate
            try:
                response = await client.post(
                    "http://localhost:8000/simulate",
                    json={"scenario": "backtest"},
                    timeout=5
                )
                results["simulate"] = "✅ PASS" if response.status_code == 200 else f"❌ {response.status_code}"
            except Exception as e:
                results["simulate"] = f"❌ {str(e)[:30]}"
        
        return results
    
    async def run_full_check(self):
        """Run comprehensive system check"""
        print("\n" + "="*70)
        print("🔍 INFINITY XOS - SYSTEM STATUS CHECK")
        print("="*70 + "\n")
        
        print(f"⏰ Timestamp: {datetime.now().isoformat()}\n")
        
        # Check services
        print("📡 SERVICE STATUS")
        print("-" * 70)
        for service_name, url in self.SERVICES.items():
            status = await self.check_service(service_name, url)
            print(f"  {service_name.upper():15} {status['status']}")
            if 'response_time' in status:
                print(f"                  Response: {status['response_time']}")
        
        print()
        
        # Check database
        print("💾 DATABASE STATUS")
        print("-" * 70)
        db_status = await self.check_database()
        if db_status.get('status') == '🟢 ONLINE':
            print(f"  {db_status.get('database')} {db_status['status']}")
            print("  Table Counts:")
            for table, count in db_status.get('tables', {}).items():
                print(f"    - {table:20} {count:>5} records")
        else:
            print(f"  {db_status['status']}: {db_status.get('error', 'Unknown')}")
        
        print()
        
        # Check compliance
        print("✅ COMPLIANCE STATUS")
        print("-" * 70)
        compliance = await self.check_compliance()
        if 'error' not in compliance:
            print(f"  Status: {compliance.get('validator', 'unknown')}")
            print(f"  Violations: {compliance.get('audit_log_entries', 0)}")
            if 'mandate_status' in compliance:
                print("  Platform Mandates:")
                for platform, status in compliance['mandate_status'].items():
                    print(f"    - {platform:10} {status}")
        else:
            print(f"  Error: {compliance.get('error')}")
        
        print()
        
        # Test key endpoints
        print("🧪 ENDPOINT TESTS")
        print("-" * 70)
        endpoints = await self.test_endpoints()
        for endpoint, result in endpoints.items():
            print(f"  POST /{endpoint:10} {result}")
        
        print()
        print("="*70)
        
        # Summary
        online_count = sum(1 for svc_name in self.SERVICES 
                          if (await self.check_service(svc_name, self.SERVICES[svc_name]))['status'].startswith('🟢'))
        total_services = len(self.SERVICES)
        
        print(f"\n📊 SUMMARY: {online_count}/{total_services} services online")
        
        if online_count == total_services:
            print("✨ All systems operational - Ready for use!")
        elif online_count == 0:
            print("❌ No services running - Start services first:")
            print("   1. python api_gateway.py (port 8000)")
            print("   2. python dashboard_api.py (port 8001)")
            print("   3. python intelligence_api.py (port 8002)")
            print("   4. python meta_service.py (port 8003)")
        else:
            print(f"⚠️  Partial system online ({online_count}/4 services)")
        
        print("\n" + "="*70 + "\n")

async def main():
    """Main entry point"""
    monitor = SystemMonitor()
    await monitor.run_full_check()

if __name__ == "__main__":
    import sys
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
        sys.exit(0)
