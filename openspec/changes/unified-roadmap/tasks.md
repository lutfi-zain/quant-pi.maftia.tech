## 1. Roadmap Documentation

- [x] 1.1 Create `ROADMAP.md` at repository root with 4 phases defined
- [x] 1.2 Add milestones with status indicators (`[ ]`, `[~]`, `[x]`) for each phase
- [x] 1.3 Document phase dependencies (1 → 2 → 3 → 4)
- [x] 1.4 Add acceptance criteria for each phase
- [x] 1.5 Update `UNIFIED_SYSTEM_ARCHITECTURE.md` roadmap section to match
- [x] 1.6 Update `README.md` roadmap table

## 2. Phase 1: Storage & ETL — Schema Design

- [x] 2.1 Design `maftia_quant.db` schema with all tables (master_ohlcv, unified_daily_analytics, unified_component_signals)
- [x] 2.2 Create SQL migration script `migrations/001_create_schema.sql`
- [x] 2.3 Add indexes for query performance (date, regime, system)
- [x] 2.4 Write schema validation tests
- [x] 2.5 Create `db.py` module with SQLite WAL connection management

## 3. Phase 1: Storage & ETL — CausalFreshnessGuard

- [x] 3.1 Implement `causal_freshness_guard.py` with stamp validation
- [x] 3.2 Add `StaleDataError` exception class
- [x] 3.3 Write unit tests for fresh data acceptance
- [x] 3.4 Write unit tests for stale data rejection
- [x] 3.5 Integrate guard into data ingestion pipeline

## 4. Phase 1: Storage & ETL — Unified OHLCV Pipeline

- [x] 4.1 Create `pipelines/ohlcv.py` with Binance API client
- [x] 4.2 Implement CausalFilter (confirmed bars only)
- [x] 4.3 Add data validation (OHLCV schema, null checks)
- [x] 4.4 Implement `master_ohlcv` table write logic
- [x] 4.5 Write integration tests with mock Binance API
- [x] 4.6 Create CLI runner `run_ohlcv_pipeline.py`

## 5. Phase 1: Storage & ETL — System Migration

- [x] 5.1 Migrate LTTD system: create `pipelines/lttd_migration.py`
- [x] 5.2 Migrate Valuation system: create `pipelines/valuation_migration.py`
- [x] 5.3 Sync MTTD data: create `pipelines/mttd_sync.py`
- [x] 5.4 Sync Ichimoku data: create `pipelines/ichimoku_sync.py`
- [x] 5.5 Write migration validation tests
- [x] 5.6 Create `run_migrate_all.py` orchestrator

## 6. Phase 1: Storage & ETL — Daily Analytics Runner

- [x] 6.1 Create `pipelines/daily_analytics.py` with MVO computation
- [x] 6.2 Add LTTD score computation with HMM regime
- [x] 6.3 Add MTTD score computation with IMO and gates
- [x] 6.4 Add Ichimoku score computation with 4 components
- [x] 6.5 Implement consensus computation with interlocking safeguards
- [x] 6.6 Add Circuit Breaker logic (MVO ≥ +1.50 → 0.0)
- [x] 6.7 Add Regime Override logic (BEAR/SIDEWAYS → 0.0)
- [x] 6.8 Write unit tests for all safeguard scenarios
- [x] 6.9 Create CLI runner `run_daily_analytics.py`
- [x] 6.10 Create cron job configuration for daily execution

## 7. Phase 2: API Gateway — Setup

- [x] 7.1 Initialize Bun project with Hono v4
- [x] 7.2 Configure TypeScript strict mode in `tsconfig.json`
- [x] 7.3 Create `src/index.ts` with Hono app setup
- [x] 7.4 Add CORS middleware
- [x] 7.5 Create SQLite connection module `src/db.ts`
- [x] 7.6 Write health check endpoint `GET /api/v1/ping`
- [x] 7.7 Add linting with Biome or ESLint

## 8. Phase 2: API Gateway — Market Endpoints

- [x] 8.1 Implement `GET /api/v1/market/ohlc` with date range query
- [x] 8.2 Implement `GET /api/v1/market/onchain` with STH metrics
- [x] 8.3 Add input validation for query parameters
- [x] 8.4 Add error handling for missing data
- [x] 8.5 Write API integration tests

## 9. Phase 2: API Gateway — System Endpoints

- [x] 9.1 Implement `GET /api/v1/valuation/composite`
- [x] 9.2 Implement `GET /api/v1/valuation/pillars`
- [x] 9.3 Implement `GET /api/v1/lttd/regime`
- [x] 9.4 Implement `GET /api/v1/lttd/score`
- [x] 9.5 Implement `GET /api/v1/lttd/exposure`
- [x] 9.6 Implement `GET /api/v1/mttd/imo`
- [x] 9.7 Implement `GET /api/v1/mttd/position`
- [x] 9.8 Implement `GET /api/v1/mttd/gates`
- [x] 9.9 Implement `GET /api/v1/ichimoku/imo`
- [x] 9.10 Implement `GET /api/v1/ichimoku/position`
- [x] 9.11 Implement `GET /api/v1/ichimoku/components`

## 10. Phase 2: API Gateway — Consensus & WebSocket

- [x] 10.1 Implement `GET /api/v1/consensus` with latest analytics
- [x] 10.2 Add interlocking safeguard logic in consensus endpoint
- [x] 10.3 Create WebSocket server at `ws://localhost:3000/ws/v1/stream`
- [x] 10.4 Implement data push on analytics update
- [x] 10.5 Add WebSocket connection management
- [x] 10.6 Write WebSocket integration tests

## 11. Phase 3: Frontend — Scaffold

- [x] 11.1 Initialize React 18 + Vite + TypeScript project
- [x] 11.2 Configure TypeScript strict mode
- [x] 11.3 Add TradingView Lightweight Charts dependency
- [x] 11.4 Create design token system in `src/styles/tokens.css`
- [x] 11.5 Add glassmorphism panel component
- [x] 11.6 Create API client module `src/api/client.ts`

## 12. Phase 3: Frontend — Executive Dashboard

- [x] 12.1 Create Dashboard layout with Bento grid
- [x] 12.2 Implement Cross-System Confluence Gauge component
- [x] 12.3 Implement Action Banner component with safeguard states
- [x] 12.4 Implement Interactive Summary Table component
- [x] 12.5 Add table sorting functionality
- [x] 12.6 Connect components to API client

## 13. Phase 3: Frontend — Charts

- [ ] 13.1 Create BTC Price Chart with Lightweight Charts
- [ ] 13.2 Add LTTD regime overlay (colored bands)
- [ ] 13.3 Add MTTD trade markers (entry/exit)
- [ ] 13.4 Add Ichimoku cloud overlay
- [ ] 13.5 Implement Vertical Crosshair Synchronization
- [ ] 13.6 Implement 85px Y-Axis Width Lock
- [ ] 13.7 Add chart responsive behavior

## 14. Phase 4: Sandboxes — Framework

- [ ] 14.1 Create sandbox router and navigation
- [ ] 14.2 Create sandbox layout component
- [ ] 14.3 Add sandbox entry points to Dashboard
- [ ] 14.4 Create shared chart components library

## 15. Phase 4: Sandboxes — Valuation Pillar Studio

- [ ] 15.1 Create Valuation Studio page component
- [ ] 15.2 Implement three-pillar display with indicator lists
- [ ] 15.3 Implement Master Oscillator chart with threshold lines
- [ ] 15.4 Add draggable threshold editor
- [ ] 15.5 Add real-time score recalculation

## 16. Phase 4: Sandboxes — LTTD Regime Lab

- [ ] 16.1 Create LTTD Lab page component
- [ ] 16.2 Implement regime timeline chart
- [ ] 16.3 Add PCA component loadings visualization
- [ ] 16.4 Add VIF heatmap
- [ ] 16.5 Add WFO fold results table

## 17. Phase 4: Sandboxes — MTTD Console

- [ ] 17.1 Create MTTD Console page component
- [ ] 17.2 Implement IMO time-series chart with gate annotations
- [ ] 17.3 Add trade markers on price chart
- [ ] 17.4 Add gate blocker heatmap

## 18. Phase 4: Sandboxes — Ichimoku Terminal

- [ ] 18.1 Create Ichimoku Terminal page component
- [ ] 18.2 Implement 4-component breakdown display
- [ ] 18.3 Add cloud overlay on price chart
- [ ] 18.4 Add SuperSmoother parameter tuner
- [ ] 18.5 Add statistical test results panel
