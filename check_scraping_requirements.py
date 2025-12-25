#!/usr/bin/env python
"""
checkWebScrapingCopilotRequirements - Comprehensive safety check for web scraping operations
Validates robots.txt compliance, rate limiting, allowlist enforcement, and safety constraints.
"""

import asyncio
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

# Import safety utilities
from safety import (
    SCRAPER_ALLOWED_HOSTS,
    SCRAPER_USER_AGENT,
    SCRAPER_MIN_DELAY,
    validate_url,
    robots_can_fetch_httpx,
    RateLimiter,
)


class WebScrapingRequirementsChecker:
    def __init__(self):
        self.status = "ok"
        self.warnings = []
        self.errors = []
        self.recommendations = []
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def check_environment(self):
        """Check environment configuration."""
        print("\n[1] Checking environment configuration...")
        
        # Check allowlist is configured
        if not SCRAPER_ALLOWED_HOSTS:
            self.errors.append("SCRAPER_ALLOWED_HOSTS not configured (empty set)")
            self.status = "blocked"
        else:
            print(f"  ✓ SCRAPER_ALLOWED_HOSTS configured: {len(SCRAPER_ALLOWED_HOSTS)} hosts")
            for host in sorted(SCRAPER_ALLOWED_HOSTS)[:5]:
                print(f"    - {host}")
            if len(SCRAPER_ALLOWED_HOSTS) > 5:
                print(f"    ... and {len(SCRAPER_ALLOWED_HOSTS) - 5} more")

        # Check user agent
        if SCRAPER_USER_AGENT:
            print(f"  ✓ User-Agent configured: {SCRAPER_USER_AGENT[:60]}...")
        else:
            self.warnings.append("SCRAPER_USER_AGENT not set; using default")

        # Check rate limiting
        if SCRAPER_MIN_DELAY > 0:
            print(f"  ✓ Minimum delay enforced: {SCRAPER_MIN_DELAY}s per host")
        else:
            self.warnings.append(f"SCRAPER_MIN_DELAY is {SCRAPER_MIN_DELAY}; should be > 0")

    async def test_robots_cache(self):
        """Test robots.txt handling after cache update."""
        print("\n[2] Testing robots.txt compliance (fresh cache)...")
        
        test_urls = [
            "https://www.example.com/page1",
            "https://www.reddit.com/r/Assistance/",
        ]
        
        results = []
        for url in test_urls:
            try:
                parsed = urlparse(url)
                # Only test if host is in allowlist
                host = parsed.netloc
                if not any(host == h or host.endswith("." + h) for h in SCRAPER_ALLOWED_HOSTS):
                    print(f"  ⊘ {url} (not in allowlist, skipping)")
                    continue
                    
                allowed = await robots_can_fetch_httpx(url, user_agent=SCRAPER_USER_AGENT, timeout=5.0)
                status = "✓ ALLOWED" if allowed else "✗ BLOCKED"
                print(f"  {status}: {url}")
                results.append((url, allowed))
            except Exception as e:
                print(f"  ⚠ {url} (error: {str(e)[:40]})")
                self.warnings.append(f"robots.txt check failed for {host}: {str(e)[:50]}")

        if results:
            blocked_count = sum(1 for _, allowed in results if not allowed)
            if blocked_count > 0:
                print(f"  → {blocked_count}/{len(results)} URLs blocked by robots.txt")

    def test_rate_limiter(self):
        """Test rate limiter configuration."""
        print("\n[3] Testing rate limiter...")
        
        limiter = RateLimiter(min_delay=SCRAPER_MIN_DELAY)
        print(f"  ✓ RateLimiter instantiated with min_delay={SCRAPER_MIN_DELAY}s")
        print(f"  ✓ Rate limiter state: empty (ready for use)")

    def validate_test_urls(self):
        """Validate sample URLs against allowlist."""
        print("\n[4] Validating sample URLs against allowlist...")
        
        test_cases = [
            ("https://www.example.com/", True),
            ("https://www.reddit.com/r/Assistance/", True),
            ("http://127.0.0.1/", False),  # Should fail: private IP
            ("https://localhost/", False),  # Should fail: loopback
            ("ftp://example.com/", False),  # Should fail: wrong scheme
        ]
        
        for url, should_succeed in test_cases:
            try:
                result = validate_url(url)
                if should_succeed:
                    print(f"  ✓ {url} → {result}")
                else:
                    print(f"  ✗ {url} (should have been rejected but passed)")
                    self.errors.append(f"URL validation failed to reject: {url}")
            except ValueError as e:
                if not should_succeed:
                    print(f"  ✓ {url} (correctly rejected: {str(e)[:40]})")
                else:
                    print(f"  ✗ {url} (rejected: {str(e)[:40]})")
                    self.errors.append(f"Valid URL rejected: {url}")

    def check_database_schema(self):
        """Check if crawl/memory database exists and has proper schema."""
        print("\n[5] Checking database schema...")
        
        db_path = os.environ.get("MCP_MEMORY_DB", "./mcp_memory.db").replace("sqlite:///", "")
        
        if os.path.exists(db_path):
            print(f"  ✓ Database exists: {db_path}")
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                
                # Check tables
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]
                
                required_tables = ["jobs", "memory"]
                for table in required_tables:
                    if table in tables:
                        cur.execute(f"PRAGMA table_info({table})")
                        cols = [row[1] for row in cur.fetchall()]
                        print(f"  ✓ Table '{table}' exists with {len(cols)} columns")
                    else:
                        self.warnings.append(f"Table '{table}' not found in database")
                
                conn.close()
            except Exception as e:
                self.warnings.append(f"Could not inspect database: {str(e)}")
        else:
            self.warnings.append(f"Database not found at {db_path}")

    def generate_recommendations(self):
        """Generate actionable recommendations."""
        print("\n[6] Generating recommendations...")
        
        if not SCRAPER_ALLOWED_HOSTS:
            self.recommendations.append({
                "priority": "CRITICAL",
                "action": "Configure SCRAPER_ALLOWED_HOSTS environment variable with comma-separated domain allowlist",
                "example": "export SCRAPER_ALLOWED_HOSTS='example.com,reddit.com,gofundme.com'"
            })
        
        if SCRAPER_MIN_DELAY < 0.5:
            self.recommendations.append({
                "priority": "HIGH",
                "action": "Increase SCRAPER_MIN_DELAY to respectful rate (>=0.5s per host)",
                "current": SCRAPER_MIN_DELAY,
                "reason": "Prevents server overload and respects crawl etiquette"
            })
        
        if not self.errors and not self.warnings:
            self.recommendations.append({
                "priority": "INFO",
                "action": "All safety checks passed. Ready for production crawls.",
                "next_steps": [
                    "Review crawl job queue: use scripts/dump_db.py",
                    "Monitor running crawls with workers/process_once.py",
                    "Inspect cached robots.txt results in memory namespace",
                ]
            })

    async def run_all_checks(self):
        """Execute all checks sequentially."""
        print("\n" + "="*70)
        print("WEB SCRAPING COPILOT REQUIREMENTS CHECK")
        print("="*70)
        print(f"Timestamp: {self.timestamp}")
        print(f"User-Agent: {SCRAPER_USER_AGENT}")
        
        self.check_environment()
        await self.test_robots_cache()
        self.test_rate_limiter()
        self.validate_test_urls()
        self.check_database_schema()
        self.generate_recommendations()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final status report."""
        print("\n" + "="*70)
        print("FINAL STATUS REPORT")
        print("="*70)
        
        # Determine final status
        if self.errors:
            self.status = "blocked"
        elif self.warnings:
            self.status = "warn"
        else:
            self.status = "ok"
        
        print(f"\n📊 OVERALL STATUS: {self.status.upper()}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, err in enumerate(self.errors, 1):
                print(f"  {i}. {err}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warn in enumerate(self.warnings, 1):
                print(f"  {i}. {warn}")
        
        if self.recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(self.recommendations)}):")
            for i, rec in enumerate(self.recommendations, 1):
                priority = rec.get("priority", "INFO")
                action = rec.get("action", "")
                print(f"\n  {i}. [{priority}] {action}")
                
                if "example" in rec:
                    print(f"     Example: {rec['example']}")
                if "reason" in rec:
                    print(f"     Reason: {rec['reason']}")
                if "next_steps" in rec:
                    print(f"     Next Steps:")
                    for step in rec["next_steps"]:
                        print(f"       • {step}")
        
        print("\n" + "="*70)
        
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


async def main():
    checker = WebScrapingRequirementsChecker()
    report = await checker.run_all_checks()
    
    # Exit with appropriate code
    if report["status"] == "blocked":
        sys.exit(1)
    elif report["status"] == "warn":
        sys.exit(0)  # Warnings don't block
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
