"""
Test Hostinger Integration
Validates Hostinger API connectivity and credential hydration
"""

import asyncio
import os
import sys

# Set path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hostinger_helper


def test_credentials():
    """Test if Hostinger credentials are configured"""
    print("Testing Hostinger credentials...")
    result = hostinger_helper.test_connection()
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    if result["status"] == "configured":
        print(f"  Key prefix: {result['key_prefix']}")
    return result["status"] == "configured"


async def test_list_domains():
    """Test listing domains"""
    print("\nTesting domain list...")
    result = await hostinger_helper.list_domains()
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
        return False
    else:
        print(f"  ✓ Success: {result.get('status')}")
        domains = result.get("domains", [])
        print(
            f"  Domains found: {len(domains) if isinstance(domains, list) else 'N/A'}"
        )
        return True


async def main():
    print("=" * 60)
    print("Hostinger Integration Test")
    print("=" * 60)

    # Test 1: Credentials
    has_creds = test_credentials()

    if not has_creds:
        print("\n⚠️  Hostinger API key not configured")
        print("   Set HOSTINGER_API_KEY environment variable or run hydrate.py")
        return

    # Test 2: List domains
    await test_list_domains()

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
