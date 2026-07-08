-- ═══════════════════════════════════════════════════════════
-- Maftia Quant — Unified Database Schema
-- Version: 1.0.0
-- Date: 2026-07-08
-- ═══════════════════════════════════════════════════════════

-- Enable WAL mode for concurrent read/write
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ═══════════════════════════════════════════════════════════
-- MASTER OHLCV TABLE (Single source for all systems)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS master_ohlcv (
    date         TEXT PRIMARY KEY,
    open         REAL NOT NULL,
    high         REAL NOT NULL,
    low          REAL NOT NULL,
    close        REAL NOT NULL,
    volume       REAL,
    source       TEXT DEFAULT 'binance',  -- 'binance' | 'yfinance'
    fetched_at   TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════
-- ON-CHAIN METRICS (From bitview.space BRK API)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS onchain_metrics (
    date                   TEXT PRIMARY KEY,
    sth_mvrv               REAL,
    sth_nupl               REAL,
    sth_sopr_24h           REAL,
    sth_supply_in_profit   REAL,
    stamp                  TEXT,
    fetched_at             TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════
-- UNIFIED DAILY ANALYTICS (All systems write here)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS unified_daily_analytics (
    date                   TEXT PRIMARY KEY,
    
    -- Valuation System outputs
    mvo_score               REAL,          -- Master Valuation Oscillator ∈ [-2, +2]
    mvo_pillar_fundamental  REAL,
    mvo_pillar_technical    REAL,
    mvo_pillar_sentiment    REAL,
    
    -- LTTD System outputs
    lttd_score              REAL,          -- ∈ [-1.0, +1.0]
    lttd_regime             TEXT,          -- 'BULL' | 'BEAR' | 'SIDEWAYS'
    lttd_p_bull             REAL,
    lttd_p_bear             REAL,
    lttd_p_sideways         REAL,
    lttd_exposure           REAL,          -- 0.0 or 1.0
    lttd_circuit_breaker    INTEGER,       -- 0 or 1
    
    -- MTTD System outputs
    mttd_imo                REAL,          -- Integrated Market Oscillator ∈ [-1, +1]
    mttd_position           REAL,          -- 0.0 or 1.0
    mttd_er                 REAL,          -- Efficiency Ratio ∈ [0, 1]
    mttd_entropy            REAL,          -- Shannon Entropy
    
    -- Ichimoku System outputs
    ichi_imo                REAL,          -- Composite Ichimoku Oscillator ∈ [-1, +1]
    ichi_position           REAL,          -- 0.0 or 1.0
    ichi_s_tk               REAL,
    ichi_s_cloud            REAL,
    ichi_s_future           REAL,
    ichi_s_chikou           REAL,
    
    -- Cross-system consensus
    consensus_score         REAL,          -- Aggregated signal
    consensus_exposure      REAL,          -- Final position ∈ {0.0, 1.0}
    
    -- Metadata
    computed_at             TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════
-- UNIFIED COMPONENT SIGNALS (Granular indicator-level data)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS unified_component_signals (
    date            TEXT,
    system          TEXT,       -- 'valuation' | 'lttd' | 'mttd' | 'ichimoku'
    component       TEXT,       -- indicator/component name
    score           REAL,       -- normalized output ∈ [-1, +1] or [-2, +2]
    raw_value       REAL,       -- pre-normalization value
    PRIMARY KEY (date, system, component)
);

-- ═══════════════════════════════════════════════════════════
-- METRIC CONFIGURATION (Thresholds and settings)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS metric_config (
    metric_name      TEXT PRIMARY KEY,
    system           TEXT,          -- 'valuation' | 'lttd' | 'mttd' | 'ichimoku'
    pillar           TEXT,          -- 'fundamental' | 'technical' | 'sentiment' (valuation only)
    description      TEXT,
    min_threshold    REAL,
    max_threshold    REAL,
    enabled          INTEGER DEFAULT 1,
    updated_at       TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════
-- WFO FOLDS (Walk-Forward Optimization results)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS wfo_folds (
    fold_id          INTEGER PRIMARY KEY,
    system           TEXT,          -- 'lttd' | 'mttd'
    train_start      TEXT,
    train_end        TEXT,
    test_start       TEXT,
    test_end         TEXT,
    test_accuracy    REAL,
    test_sharpe      REAL,
    lambda_          REAL,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════
-- INDICATOR SCORES (LTTD system indicator outputs)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS indicator_scores (
    date             TEXT,
    indicator_name   TEXT,
    score            INTEGER,      -- -1 or +1
    PRIMARY KEY (date, indicator_name)
);

-- ═══════════════════════════════════════════════════════════
-- INDEXES for query performance
-- ═══════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_ohlcv_date ON master_ohlcv(date);
CREATE INDEX IF NOT EXISTS idx_onchain_date ON onchain_metrics(date);
CREATE INDEX IF NOT EXISTS idx_unified_date ON unified_daily_analytics(date);
CREATE INDEX IF NOT EXISTS idx_unified_regime ON unified_daily_analytics(lttd_regime);
CREATE INDEX IF NOT EXISTS idx_signals_system ON unified_component_signals(system);
CREATE INDEX IF NOT EXISTS idx_signals_system_date ON unified_component_signals(system, date);
CREATE INDEX IF NOT EXISTS idx_config_system ON metric_config(system);
CREATE INDEX IF NOT EXISTS idx_wfo_system ON wfo_folds(system);
CREATE INDEX IF NOT EXISTS idx_indicator_date ON indicator_scores(date);

-- ═══════════════════════════════════════════════════════════
-- VIEWS for common queries
-- ═══════════════════════════════════════════════════════════

-- Latest analytics row (for API /consensus endpoint)
CREATE VIEW IF NOT EXISTS v_latest_analytics AS
SELECT * FROM unified_daily_analytics
ORDER BY date DESC LIMIT 1;

-- Current regime status
CREATE VIEW IF NOT EXISTS v_current_regime AS
SELECT 
    date,
    lttd_regime,
    lttd_p_bull,
    lttd_p_bear,
    lttd_p_sideways,
    lttd_exposure,
    lttd_circuit_breaker
FROM unified_daily_analytics
ORDER BY date DESC LIMIT 1;

-- Current consensus
CREATE VIEW IF NOT EXISTS v_current_consensus AS
SELECT
    date,
    consensus_score,
    consensus_exposure,
    mvo_score,
    lttd_regime,
    mttd_position,
    ichi_position
FROM unified_daily_analytics
ORDER BY date DESC LIMIT 1;
