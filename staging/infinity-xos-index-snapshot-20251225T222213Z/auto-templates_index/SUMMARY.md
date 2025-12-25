# auto-templates/index

Path: auto-templates/index

Snapshots: 3

## README.md snippet:

# Infinity XOS Global Index (Tier-0)

**Enterprise-Grade Global Index & Capabilities Registry for Infinity XOS / fullauto.systems**

The Global Index is the **Tier-0 foundational service** that provides a single source of truth for:

- All repositories and services across the Infinity XOS ecosystem
- All capabilities and actions available across the platform
- Service dependency graphs and architecture visualization
- Machine-readable API specifications (OpenAPI 3.1) for agents, gateways, and integrations

## 🎯 Purpose

This service is the **first point of discovery** for:

- **Aura AI** (voice assistant) - discovering available actions
- **Omni Gateway** - routing requests to appropriate services
- **Auto-Engineer** and other agents - finding capabilities and APIs
- **ChatGPT Actions** - OpenAI JSON integration via OpenAPI specs
- **Google Workspace** integrations - calendar, email, tasks, drive
- **Social integrations** - posting, analytics
- **ML/AI workflows** - image generation, text analysis

## 🏗️ Architecture

```
index/
├── config/
│   ├── repos.yml          # 37 repositories with metadata
│   └── actions.yml        # 12 capabilities, 12+ actions
├── schemas/
│   ├── repos/             # JSON Schema for repo validation
│   ├── capabilities/      # JSON Schema for capability validation
│   └── actions/           # JSON Schema for action validation + samples
├── src/
│   ├── cli/               # CLI tool for local queries
│   ├── server/            # HTTP API service
│   ├── utils/             # Loader and validator utilities
│   ├── generators/        # OpenAPI and graph generators
│   └── types/             # TypeScript type definitions

## Files (top-level):
- .dockerignore
- .eslintrc.cjs
- .git
- .github
- .gitignore
- .prettierrc
- .pytest_cache
- actions.yml
- auto-docs-sync
- config
- CONFIG.md
- docker-compose.dev.yml
- docker-compose.yml
- DOCKER.md
- Dockerfile
- Dockerfile.dev
- docs
- eslint.config.mjs
- jest.config.js
- jest.config.ts
- package-lock.json
- package.json
- README.md
- repos.yml
- schemas
- SECURITY.md
- src
- tests
- tsconfig.json