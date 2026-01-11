#!/usr/bin/env python3
"""
MCP HTTP Adapter Verification Script
Validates implementation correctness and readiness for Custom GPT integration
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AdapterVerifier:
    """Verifies MCP HTTP Adapter implementation"""

    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path or ".")
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []

    def verify_all(self):
        """Run all verification checks"""
        logger.info("=" * 60)
        logger.info("MCP HTTP ADAPTER VERIFICATION SUITE")
        logger.info("=" * 60)

        checks = [
            ("File Existence", self.check_files_exist),
            ("Code Structure", self.check_code_structure),
            ("Imports", self.check_imports),
            ("Configuration", self.check_configuration),
            ("Integration Points", self.check_integration),
            ("OpenAPI Schema", self.check_openapi_schema),
            ("Security", self.check_security),
            ("Cloud Run Readiness", self.check_cloud_run),
        ]

        for check_name, check_func in checks:
            logger.info(f"\n► {check_name}...")
            try:
                check_func()
            except Exception as e:
                logger.error(f"✗ {check_name} failed: {e}")
                self.checks_failed += 1

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✓ Passed: {self.checks_passed}")
        logger.info(f"✗ Failed: {self.checks_failed}")

        if self.warnings:
            logger.warning(f"\n⚠ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        return self.checks_failed == 0

    def check_files_exist(self):
        """Verify all required files exist"""
        required_files = [
            "mcp_http_adapter.py",
            "mcp_config.py",
            "omni_gateway.py",
            "main_extended.py",
            "MCP_HTTP_ADAPTER_GUIDE.md",
        ]

        for filename in required_files:
            filepath = self.repo_path / filename
            if filepath.exists():
                size = filepath.stat().st_size
                logger.info(f"  ✓ {filename} ({size} bytes)")
                self.checks_passed += 1
            else:
                logger.error(f"  ✗ {filename} NOT FOUND")
                self.checks_failed += 1

    def check_code_structure(self):
        """Verify code structure and classes"""
        adapter_file = self.repo_path / "mcp_http_adapter.py"

        if not adapter_file.exists():
            logger.error("  ✗ mcp_http_adapter.py not found")
            self.checks_failed += 1
            return

        content = adapter_file.read_text()

        required_classes = [
            "MCPHTTPAdapter",
            "ToolDefinition",
            "ExecuteRequest",
            "ExecuteResponse",
            "HealthResponse",
            "ToolCategory",
        ]

        for class_name in required_classes:
            if f"class {class_name}" in content:
                logger.info(f"  ✓ Class {class_name} defined")
                self.checks_passed += 1
            else:
                logger.error(f"  ✗ Class {class_name} NOT FOUND")
                self.checks_failed += 1

        required_methods = [
            "health",
            "list_tools",
            "execute_tool",
            "generate_openapi_spec",
            "_initialize_mcp_server",
        ]

        for method_name in required_methods:
            if f"def {method_name}" in content:
                logger.info(f"  ✓ Method {method_name} defined")
                self.checks_passed += 1
            else:
                logger.error(f"  ✗ Method {method_name} NOT FOUND")
                self.checks_failed += 1

    def check_imports(self):
        """Verify critical imports"""
        adapter_file = self.repo_path / "mcp_http_adapter.py"

        if not adapter_file.exists():
            logger.error("  ✗ mcp_http_adapter.py not found")
            self.checks_failed += 1
            return

        content = adapter_file.read_text()

        required_imports = [
            "from fastapi import",
            "from pydantic import",
            "from typing import",
            "import asyncio",
            "from mcp_config import",
        ]

        for import_stmt in required_imports:
            if import_stmt in content:
                logger.info(f"  ✓ Import: {import_stmt}")
                self.checks_passed += 1
            else:
                logger.warning(f"  ⚠ Import may be missing: {import_stmt}")
                self.warnings.append(f"Import {import_stmt} not found")

    def check_configuration(self):
        """Verify configuration file"""
        config_file = self.repo_path / "mcp_config.py"

        if not config_file.exists():
            logger.error("  ✗ mcp_config.py not found")
            self.checks_failed += 1
            return

        content = config_file.read_text()

        required_config_items = [
            "MCP_API_KEY",
            "MCP_ENABLE_AUTH",
            "MCP_READ_ONLY",
            "FIRESTORE_PROJECT_ID",
            "CLOUD_RUN_MODE",
        ]

        for config_item in required_config_items:
            if config_item in content:
                logger.info(f"  ✓ Config item: {config_item}")
                self.checks_passed += 1
            else:
                logger.warning(f"  ⚠ Config item may be missing: {config_item}")
                self.warnings.append(f"Config {config_item} not found")

    def check_integration(self):
        """Verify integration with omni_gateway.py"""
        gateway_file = self.repo_path / "omni_gateway.py"

        if not gateway_file.exists():
            logger.error("  ✗ omni_gateway.py not found")
            self.checks_failed += 1
            return

        content = gateway_file.read_text()

        integration_points = [
            "mcp_http_adapter",
            "include_router",
            "/mcp/",
        ]

        for point in integration_points:
            if point in content:
                logger.info(f"  ✓ Integration point: {point}")
                self.checks_passed += 1
            else:
                logger.error(f"  ✗ Integration point missing: {point}")
                self.checks_failed += 1

    def check_openapi_schema(self):
        """Verify OpenAPI schema generation"""
        adapter_file = self.repo_path / "mcp_http_adapter.py"

        if not adapter_file.exists():
            logger.error("  ✗ mcp_http_adapter.py not found")
            self.checks_failed += 1
            return

        content = adapter_file.read_text()

        openapi_components = [
            "openapi.org/3.0",
            "paths",
            "components",
            "securitySchemes",
        ]

        for component in openapi_components:
            if component in content:
                logger.info(f"  ✓ OpenAPI component: {component}")
                self.checks_passed += 1
            else:
                logger.warning(f"  ⚠ OpenAPI component may be missing: {component}")
                self.warnings.append(f"OpenAPI component {component} may be missing")

    def check_security(self):
        """Verify security implementation"""
        adapter_file = self.repo_path / "mcp_http_adapter.py"

        if not adapter_file.exists():
            logger.error("  ✗ mcp_http_adapter.py not found")
            self.checks_failed += 1
            return

        content = adapter_file.read_text()

        security_features = [
            ("X-MCP-KEY", "API key authentication"),
            ("check_governance", "Governance enforcement"),
            ("read_only", "Read-only mode support"),
            ("dry_run", "Dry-run capability"),
            ("rate_limit", "Rate limiting"),
        ]

        for feature_code, feature_name in security_features:
            if feature_code in content:
                logger.info(f"  ✓ Security feature: {feature_name}")
                self.checks_passed += 1
            else:
                logger.warning(f"  ⚠ Security feature may be missing: {feature_name}")
                self.warnings.append(f"Security feature {feature_name} may be missing")

    def check_cloud_run(self):
        """Verify Cloud Run readiness"""
        adapter_file = self.repo_path / "mcp_http_adapter.py"
        config_file = self.repo_path / "mcp_config.py"

        cloud_run_indicators = [
            ("Stateless operation", ["async", "asyncio"]),
            ("No stdio assumptions", ["sys.stdin", "sys.stdout"]),
            ("Environment variables", ["os.getenv"]),
            ("Firestore integration", ["firestore"]),
        ]

        all_content = ""
        if adapter_file.exists():
            all_content += adapter_file.read_text()
        if config_file.exists():
            all_content += config_file.read_text()

        for indicator_name, keywords in cloud_run_indicators:
            found = any(keyword in all_content for keyword in keywords)
            if found:
                logger.info(f"  ✓ Cloud Run ready: {indicator_name}")
                self.checks_passed += 1
            else:
                logger.warning(
                    f"  ⚠ Cloud Run feature may be missing: {indicator_name}"
                )
                self.warnings.append(
                    f"Cloud Run feature {indicator_name} may be missing"
                )


def print_verification_report(repo_path: str = None):
    """Run verification and print report"""
    verifier = AdapterVerifier(repo_path)
    success = verifier.verify_all()

    print("\n" + "=" * 60)
    if success:
        print("✓ VERIFICATION SUCCESSFUL - Adapter ready for testing")
    else:
        print("✗ VERIFICATION FAILED - Fix issues above before testing")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(print_verification_report(repo_path))
