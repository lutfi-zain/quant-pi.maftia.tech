## ADDED Requirements

### Requirement: Unified SQLite Schema

The system SHALL have a `maftia_quant.db` SQLite database with WAL mode enabled, containing tables for all 4 systems.

#### Scenario: Database file exists

- **WHEN** Phase 1 is complete
- **THEN** `maftia_quant.db` exists with WAL mode enabled

#### Scenario: Master OHLCV table

- **WHEN** developer queries `master_ohlcv` table
- **THEN** table contains `date`, `open`, `high`, `low`, `close`, `volume`, `source`, `fetched_at` columns

#### Scenario: Unified daily analytics table

- **WHEN** developer queries `unified_daily_analytics` table
- **THEN** table contains columns for MVO, LTTD, MTTD, Ichimoku, and consensus outputs

#### Scenario: Component signals table

- **WHEN** developer queries `unified_component_signals` table
- **THEN** table contains `date`, `system`, `component`, `score`, `raw_value` columns

### Requirement: CausalFreshnessGuard

The system SHALL validate all BRK data ingestion using CausalFreshnessGuard.

#### Scenario: Fresh data accepted

- **WHEN** BRK API response has `stamp >= yesterday`
- **THEN** data is accepted and stored in database

#### Scenario: Stale data rejected

- **WHEN** BRK API response has `stamp < yesterday`
- **THEN** system raises `StaleDataError` and rejects the data

### Requirement: Unified OHLCV Pipeline

The system SHALL have a unified OHLCV pipeline that fetches BTC/USD daily data from Binance.

#### Scenario: Data fetch succeeds

- **WHEN** pipeline runs
- **THEN** system fetches daily OHLCV from Binance API for BTCUSDT

#### Scenario: CausalFilter applied

- **WHEN** pipeline processes raw data
- **THEN** only confirmed bars are stored (no lookahead bias)

#### Scenario: Data stored in master table

- **WHEN** pipeline completes
- **THEN** data is written to `master_ohlcv` table with `source = 'binance'`

### Requirement: Cross-System Daily Analytics Runner

The system SHALL have a daily runner that computes analytics for all 4 systems and writes to `unified_daily_analytics`.

#### Scenario: Runner executes

- **WHEN** daily runner is triggered
- **THEN** system computes MVO, LTTD, MTTD, and Ichimoku scores for current date

#### Scenario: Consensus computed

- **WHEN** all 4 systems have scores for current date
- **THEN** system computes `consensus_exposure` applying interlocking safeguards

#### Scenario: Interlocking safeguards applied

- **WHEN** consensus is computed
- **THEN** Circuit Breaker (MVO ≥ +1.50) forces exposure to 0.0
- **THEN** Regime Override (BEAR/SIDEWAYS) forces MTTD + Ichimoku to 0.0
