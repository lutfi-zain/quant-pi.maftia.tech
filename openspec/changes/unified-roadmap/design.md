## Context

The Maftia Quant platform currently exists as 4 separate documentation repositories with no unified codebase:

| System | Current State | Target State |
|--------|--------------|--------------|
| Valuation | `metrics.db` + Hono API `:3000` | Unified `maftia_quant.db` |
| LTTD | `lttd.db` + Hono API `:8765` | Unified `maftia_quant.db` |
| MTTD | `btc_daily.json` + CSV files | Unified `maftia_quant.db` |
| Ichimoku | yfinance cache + FastAPI `:8000` | Unified `maftia_quant.db` |

**Current pain points:**

- 4 separate databases with no cross-system queries
- 3 different API frameworks (Hono, Hono, FastAPI)
- No unified frontend — each system has its own dashboard
- Interlocking safeguards implemented inconsistently
- No shared data ingestion pipeline

## Goals / Non-Goals

**Goals:**

1. Unified `maftia_quant.db` schema supporting all 4 systems
2. Single Hono v4 API gateway on Bun serving all endpoints
3. Single React frontend with Executive Dashboard + 4 sandboxes
4. Interlocking safeguards implemented at API layer
5. Phased migration with rollback capability per phase

**Non-Goals:**

- Real-time trading execution (analysis only)
- Mobile app development
- Multi-asset support (Bitcoin only)
- Cloud deployment (local-first, Docker optional)
- Historical backtesting engine (existing per-system backtests remain)

## Decisions

### D1: Sequential Phase Execution (not parallel)

**Decision:** Execute phases sequentially (1 → 2 → 3 → 4), not in parallel.

**Rationale:**

- Phase 1 (schema) must complete before Phase 2 (API) can serve data
- Phase 2 (API) must complete before Phase 3 (frontend) can display live data
- Phase 4 (sandboxes) depends on Phase 3 framework

**Alternatives considered:**

- Parallel execution: Risk of schema mismatches between systems
- Bottom-up (frontend first): Would require mock data, wasted effort

### D2: SQLite WAL (not PostgreSQL)

**Decision:** Keep SQLite WAL as the unified storage layer.

**Rationale:**

- Zero-config deployment
- WAL mode provides sufficient concurrency for single-machine pipeline
- All 4 existing systems already use SQLite
- Sufficient for analytical workloads (not OLTP)

**Alternatives considered:**

- PostgreSQL: Overkill for single-machine, adds deployment complexity
- DuckDB: Good for analytics but immature ecosystem

### D3: Hono v4 on Bun (not Express/Fastify)

**Decision:** Use Hono v4 on Bun runtime for the unified API.

**Rationale:**

- 3-5× faster than Node.js for JSON serving
- Native TypeScript support
- Edge-ready (Cloudflare Workers compatible)
- Minimal footprint, fast cold starts

**Alternatives considered:**

- Express: Slower, older patterns
- Fastify: Good performance but heavier ecosystem
- FastAPI: Python-only, already used by Ichimoku but inconsistent with other systems

### D4: Interlocking Safeguards at API Layer

**Decision:** Implement Circuit Breaker and Regime Override logic in the API gateway, not per-system.

**Rationale:**

- Single source of truth for safeguard state
- Prevents inconsistent safeguard implementation
- Easier to audit and test
- Frontend receives pre-computed consensus

**Alternatives considered:**

- Per-system safeguards: Risk of inconsistency, harder to audit
- Frontend-only safeguards: Security risk, client-side bypass possible

### D5: Phased Migration (not big-bang)

**Decision:** Migrate systems one phase at a time, not all at once.

**Rationale:**

- Each phase is independently testable
- Rollback is simple (revert to previous phase)
- Reduces risk of catastrophic failure
- Allows learning from early phases

**Alternatives considered:**

- Big-bang migration: High risk, hard to debug
- Per-system migration: Doesn't address cross-system dependencies

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Schema changes break existing systems | Phase 1 includes backward-compatible views |
| API performance degradation | Load test each phase before proceeding |
| Frontend complexity explosion | Modular sandbox architecture, lazy loading |
| Data loss during migration | Backup before each phase, WAL checkpoint |
| Interlocking safeguards bypassed | API-layer implementation, unit tests for all scenarios |

## Migration Plan

### Phase 1: Storage & ETL (Weeks 1-3)

1. Design `maftia_quant.db` schema with all 4 systems' tables
2. Implement CausalFreshnessGuard
3. Create unified OHLCV pipeline from Binance
4. Migrate LTTD system to unified schema
5. Migrate Valuation system to unified schema
6. Sync MTTD data to SQLite
7. Sync Ichimoku data to SQLite
8. Create cross-system daily analytics runner

### Phase 2: API Gateway (Weeks 4-6)

1. Hono v4 project setup on Bun
2. Implement `/api/v1/market/*` endpoints
3. Implement `/api/v1/valuation/*` endpoints
4. Implement `/api/v1/lttd/*` endpoints
5. Implement `/api/v1/mttd/*` endpoints
6. Implement `/api/v1/ichimoku/*` endpoints
7. Implement `/api/v1/consensus` endpoint
8. Add WebSocket streaming

### Phase 3: Frontend Core (Weeks 7-10)

1. React + Vite + TypeScript scaffold
2. Design token system (HSL CSS variables)
3. Executive Dashboard layout (Bento grid)
4. Cross-System Confluence Gauge
5. Action Banner component
6. Interactive Summary Table
7. BTC Price Chart with regime overlay
8. Vertical Crosshair Synchronization
9. 85px Y-Axis Width Lock

### Phase 4: Advanced Sandboxes (Weeks 11-16)

1. Valuation Pillar Studio
2. LTTD Orthogonal Regime Lab
3. MTTD Console
4. Ichimoku Terminal

## Open Questions

1. **Deployment target:** Local-only or Docker containerization?
2. **Authentication:** API key for external access, or local-only?
3. **Data refresh schedule:** Daily cron job or manual trigger?
4. **Historical data depth:** How far back to backfill? (2016+ recommended)
5. **Sandbox framework:** Shared component library or per-sandbox isolated?
