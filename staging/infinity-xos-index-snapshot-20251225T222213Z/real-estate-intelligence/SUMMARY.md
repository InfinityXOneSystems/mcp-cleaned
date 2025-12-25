# real-estate-intelligence

Path: real-estate-intelligence

Snapshots: 19

## README.md snippet:

﻿# Real Estate Intelligence

This repository is the **Real Estate Intelligence execution surface** within the Infinity X One Systems ecosystem.

It contains:
- Domain-specific agents and workflows
- Cloud Run–deployable services
- Persistent memory services
- Validation and workflow artifacts
- Industry-facing orchestration logic

This repo is designed to **execute**, not to define global cognition or platform-wide policy.

---

## Architecture Overview

The system is organized around a clear separation of concerns:

- **Services**: Executable Cloud Run services (memory, gateway, crawler, agents)
- **Agents**: Domain operators that perform reasoning and execution
- **Memory**: Persistent, Cloud Run–hosted memory service
- **Workflows & Templates**: First-class operational artifacts
- **Validation**: Platform and contract validation utilities

All components in this repo are deployable and operational.

---

## Vision Cortex (Cognitive Submodule)

The `vision-cortex/` directory is included as a **Git submodule**.

**Vision Cortex is the shared cognitive engine** used for advanced reasoning and decision support across Infinity X One Systems.

### Important Rules

- `vision-cortex/` is **read-only** in this repository
- Do **NOT** modify Vision Cortex code here
- All Vision Cortex changes must be made in its own repository

## Files (top-level):
- $null
- .dockerignore
- .env.example
- .eslintrc.json
- .foundation_status.json
- .genesis.json
- .git
- .gitattributes
- .github
- .gitignore
- .gitmodules
- .infinityxos_root
- .vscode
- agents
- auto-docs-sync
- autonomy
- AUTONOMY_DISABLED
- AUTONOMY_ENABLED
- AUTONOMY_LEDGER.md
- AUTO_BOOT.ps1
- AUTO_BOOT_LLM.ps1
- bootstrap
- cloudrun.crawler.yaml
- cloudrun.yaml
- CODE_SNAPSHOT.txt
- desktop.ini
- doc-evolution-system
- docker-compose.yml
- Dockerfile
- docs
- executors
- frontend
- gateway
- helix
- ingest_test.json
- intelligence
- llm
- logs
- orchestrator
- platform-validator.ps1
- pyproject.toml
- README.md
- router
- RUNTIME.md
- scripts
- services
- taxonomy_contract
- templates and docs
- templates and docs.zip
- vision-cortex
- work flow
- _foundation_backup_20251215-111350
- _index_snapshot.txt