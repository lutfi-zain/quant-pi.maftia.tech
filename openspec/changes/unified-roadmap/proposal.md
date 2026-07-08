## Why

The Maftia Quant platform currently exists as documentation across 4 separate systems (Valuation, LTTD, MTTD, Ichimoku) with no unified implementation roadmap. We need a master roadmap document that:

1. Establishes the phased migration strategy from 4 separate repos → 1 unified platform
2. Defines clear deliverables, dependencies, and acceptance criteria per phase
3. Serves as the parent OpenSpec change that spawns child proposals for each phase
4. Provides a single source of truth for project status and priorities

Without this roadmap, implementation risks becoming fragmented, with systems built in isolation rather than as an interlocking whole.

## What Changes

- **NEW:** `ROADMAP.md` — Master implementation roadmap with 4 phases, ~20 milestones
- **NEW:** Phase-level OpenSpec proposals spawned from this roadmap:
  - Phase 1: Storage & ETL (maftia_quant.db schema, unified pipelines)
  - Phase 2: API Gateway (Hono v4 on Bun, REST + WebSocket)
  - Phase 3: Frontend Core (Executive Dashboard, crosshair sync, y-axis lock)
  - Phase 4: Advanced Sandboxes (4 deep-dive workspaces)
- **UPDATED:** `UNIFIED_SYSTEM_ARCHITECTURE.md` — Roadmap section aligned with new phases
- **UPDATED:** `README.md` — Roadmap table reflects actual implementation phases

## Capabilities

### New Capabilities

- `master-roadmap`: Central roadmap document defining all implementation phases, milestones, dependencies, and success criteria. Parent change that spawns child OpenSpec proposals.
- `phase1-storage-etl`: Unified SQLite WAL schema, CausalFreshnessGuard, OHLCV pipeline, cross-system daily analytics runner
- `phase2-api-gateway`: Hono v4 REST API on Bun, all `/api/v1/*` endpoints, WebSocket streaming
- `phase3-frontend-core`: React + Vite, Executive Dashboard, Bento grid, crosshair sync, y-axis lock
- `phase4-sandboxes`: 4 deep-dive workspaces (Valuation Studio, LTTD Lab, MTTD Console, Ichimoku Terminal)

### Modified Capabilities

(none — this is a new repository structure)

## Impact

**Systems Affected:** All 4 systems must be migrated in sequence

- Valuation System → Phase 1 (schema) + Phase 2 (API)
- LTTD System → Phase 1 (schema) + Phase 2 (API) + Phase 3 (regime overlay)
- MTTD System → Phase 1 (schema) + Phase 2 (API) + Phase 3 (trade markers)
- Ichimoku Terminal → Phase 1 (schema) + Phase 2 (API) + Phase 3 (cloud overlay)

**Interlocking Safeguards:** Phase 2 must implement Circuit Breaker and Regime Override logic in the API layer before any frontend can display live consensus.

**Database Schema:** `maftia_quant.db` must be designed in Phase 1 with all 4 systems' tables before any API endpoints can serve data.

**Dependencies:**

- Phase 1 → Phase 2 → Phase 3 → Phase 4 (sequential)
- Phase 2 and 3 can partially parallelize (API endpoints + frontend scaffolding)
- Phase 4 depends on Phase 3 completion (sandboxes use dashboard framework)

**Rollback:** Each phase is independently deployable. If Phase 3 fails, Phase 2 API remains functional.
