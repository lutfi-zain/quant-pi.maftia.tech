## ADDED Requirements

### Requirement: Hono v4 API Server

The system SHALL have a Hono v4 API server running on Bun runtime.

#### Scenario: Server starts

- **WHEN** developer runs `bun run dev`
- **THEN** API server starts on port 3000

#### Scenario: Health check endpoint

- **WHEN** client sends `GET /api/v1/ping`
- **THEN** server responds with `{"status": "ok"}` and 200 status

### Requirement: Market Endpoints

The API SHALL serve unified market data endpoints.

#### Scenario: OHLCV endpoint

- **WHEN** client sends `GET /api/v1/market/ohlc?from=2024-01-01&to=2024-12-31`
- **THEN** server returns `{"data": [...]}` with OHLCV rows from `master_ohlcv`

#### Scenario: On-chain metrics endpoint

- **WHEN** client sends `GET /api/v1/market/onchain`
- **THEN** server returns STH MVRV, NUPL, SOPR, and Supply-in-Profit data

### Requirement: System-Specific Endpoints

The API SHALL serve endpoints for each quantitative system.

#### Scenario: Valuation composite endpoint

- **WHEN** client sends `GET /api/v1/valuation/composite`
- **THEN** server returns MVO score time-series

#### Scenario: LTTD regime endpoint

- **WHEN** client sends `GET /api/v1/lttd/regime`
- **THEN** server returns current regime (BULL/BEAR/SIDEWAYS) and posterior probabilities

#### Scenario: MTTD IMO endpoint

- **WHEN** client sends `GET /api/v1/mttd/imo`
- **THEN** server returns IMO score ∈ [-1, +1]

#### Scenario: Ichimoku position endpoint

- **WHEN** client sends `GET /api/v1/ichimoku/position`
- **THEN** server returns current position (0.0 or 1.0)

### Requirement: Consensus Endpoint

The API SHALL serve a consensus endpoint that applies interlocking safeguards.

#### Scenario: Consensus computation

- **WHEN** client sends `GET /api/v1/consensus`
- **THEN** server returns latest row from `unified_daily_analytics` with all system scores

#### Scenario: Circuit breaker active

- **WHEN** MVO score ≥ +1.50
- **THEN** consensus endpoint returns `consensus_exposure = 0.0`

#### Scenario: Regime override active

- **WHEN** LTTD regime is BEAR or SIDEWAYS
- **THEN** consensus endpoint returns `mttd_position = 0.0` and `ichi_position = 0.0`

### Requirement: WebSocket Streaming

The API SHALL support WebSocket streaming for real-time updates.

#### Scenario: WebSocket connection

- **WHEN** client connects to `ws://localhost:3000/ws/v1/stream`
- **THEN** server establishes WebSocket connection

#### Scenario: Data push

- **WHEN** new daily analytics are computed
- **THEN** server pushes updated consensus to all connected clients
