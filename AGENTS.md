# AGENTS.md

**Repository:** `quant-pi.maftia.tech`
**Domain:** Unified Bitcoin Quantitative Intelligence Platform — 4 Systems Merged into 1
**Version:** 1.0.0

This file is the authoritative guide for AI coding agents working in this repository. It defines the layered architecture, code style rules, and hard constraints that every change must satisfy.

> ⚠️ **CRITICAL:** This is currently a **documentation-only repository**. Code implementations live in separate repos (see [Systems](#systems) below). When code is added, update this file with test commands.

---

## Systems

| # | System | Horizon | Key Method | Repository |
|---|--------|---------|------------|------------|
| 1 | **Valuation System** | Macro Cycle (multi-year) | 17-indicator MVO piecewise [-2,+2] | `quant-btc-valuation-system` |
| 2 | **LTTD System** | Long-Term (120–350 days) | 3-State HMM + PCA + XGBoost | `quant-btc-lttd-system` |
| 3 | **MTTD System** | Medium-Term (10–120 days) | Multi-principle consensus + IMO | `quant-btc-mttd-system` |
| 4 | **Ichimoku Terminal** | Medium-Term (10–60 days) | tanh Ichimoku + SuperSmoother | `quant-lttd-ichimoku` |

> 🚫 **IGNORED:** `quant-technical-indicator-bank` — documentation and references removed from this project.

---

## Commands

```bash
# Documentation-only repository — no test command yet
# When code is added, update this section with:
# pytest --cov --cov-report=html
# bun test
```

Run all tests and confirm they pass before finalising any change.

---

## Project Context & Business Domain (DDD)

**Ubiquitous Language:**

| Term | Definition | Systems |
|------|-----------|---------|
| **MVO** | Master Valuation Oscillator ∈ [-2, +2] — macro cycle valuation score | Valuation |
| **LTTD** | Long-Term Trend Direction — 120-350 day regime classification | LTTD |
| **MTTD** | Medium-Term Trend Direction — 10-120 day trend following | MTTD |
| **IMO** | Integrated Market Oscillator — composite Ichimoku signal ∈ [-1, +1] | MTTD, Ichimoku |
| **Regime** | HMM state: `BULL` / `BEAR` / `SIDEWAYS` | LTTD |
| **Circuit Breaker** | MVO ≥ +1.50 → all systems forced to 0.0 exposure | Valuation → All |
| **Regime Override** | LTTD BEAR/SIDEWAYS → MTTD + Ichimoku forced to 0.0 | LTTD → MTTD, Ichimoku |
| **CausalFilter** | Zero lookahead bias — only past bars referenced | All |
| **OU Half-Life** | Ornstein-Uhlenbeck mean-reversion speed (120-350d post-2020) | LTTD |
| **PCA** | Principal Component Analysis — eliminates multicollinearity | LTTD |
| **VIF** | Variance Inflation Factor > 10 → drop feature | LTTD |
| **Kaufman ER** | Efficiency Ratio — trend strength vs random walk ∈ [0, 1] | MTTD, Ichimoku |
| **Shannon Entropy** | Information-theoretic noise gate ∈ [0, log₂(bins)] | MTTD, Ichimoku |
| **tanh** | Hyperbolic tangent — maps real → [-1, +1] bounded | MTTD, Ichimoku |
| **SuperSmoother** | Ehlers 2-pole IIR filter — noise reduction without lag | MTTD, Ichimoku |
| **WFO** | Walk-Forward Optimization — rolling train/validate/test | LTTD, MTTD |

**Additional Terms:**

| Term | Definition |
|------|-----------|
| **Piecewise Normalization** | Linear interpolation against historical SD thresholds → [-2, +2] |
| **Binary Hysteresis** | Position is always exactly 0.0 or 1.0 — no fractional sizing |
| **Consensus Exposure** | Final position = intersection of all system constraints |
| **STH Metrics** | Short-Term Holder: MVRV, NUPL, SOPR, Supply-in-Profit |
| **maftia_quant.db** | Unified SQLite WAL database — single source of truth |
| **Hono** | Bun-native web framework for API Gateway |
| **Lightweight Charts** | TradingView charting library for frontend |

Ensure all variable names, database columns, and API responses strictly adhere to this ubiquitous language.

---

## Architecture Boundaries (Progressive Disclosure)

Logic flows strictly according to the defined architectural patterns. For the canonical implementation patterns, refer to these Gold Standard files:

- **Master Architecture:** [UNIFIED_SYSTEM_ARCHITECTURE.md](./UNIFIED_SYSTEM_ARCHITECTURE.md) — Interlocking matrix, schema design, API endpoints, UI/UX tokens
- **Most Rigorous System:** [docs/02_quant_btc_lttd_system.md](./docs/02_quant_btc_lttd_system.md) — 6-layer architecture, HMM, PCA, WFO, CausalFilter
- **Best Statistical Validation:** [docs/04_quant_lttd_ichimoku.md](./docs/04_quant_lttd_ichimoku.md) — 5 formal tests (ADF, KS, t-test, Bootstrap, Bonferroni)

*Agents: Do not hallucinate structural patterns. Read the Gold Standard files before creating new components.*

---

## Interlocking Safeguards (NEVER BYPASS)

The interlocking matrix is the core innovation. These safeguards prevent catastrophic risk:

| Priority | Condition | Source | Target | Action |
|----------|-----------|--------|--------|--------|
| **TIER 1** | `MVO ≥ +1.50` | Valuation | ALL systems | Circuit Breaker → 0.0 exposure |
| **TIER 1** | `MVO ≤ -2.03` | Valuation | LTTD | Deep Value Override → 1.0 exposure |
| **TIER 2** | `Regime = BEAR` | LTTD | MTTD, Ichimoku | Regime Override → 0.0 exposure |
| **TIER 2** | `Regime = SIDEWAYS` | LTTD | MTTD, Ichimoku | Regime Override → 0.0 exposure |
| **TIER 3** | `ER < 0.20` | MTTD, Ichimoku | Self | Gate blocked → 0.0 exposure |
| **TIER 3** | `Entropy > 2.30` | MTTD, Ichimoku | Self | Gate blocked → 0.0 exposure |

**Rule:** Any system can veto to 0.0, but NO system can override to 1.0 alone.

---

## Security & Compliance Guardrails

### Hard Constraints (NEVER violate)

- **CausalFilter is MANDATORY.** Every indicator, signal, and computation must only reference past bars. Zero lookahead bias. No symmetric windows. No future data leakage.
- **Circuit Breakers are UNBYPASSABLE.** When MVO ≥ +1.50, ALL trend-following systems MUST hold 0.0 exposure. No exceptions. No "small" overrides.
- **Regime Override is MANDATORY.** When LTTD Regime = BEAR or SIDEWAYS, MTTD and Ichimoku MUST hold 0.0 exposure.
- **VIF > 10 is FORBIDDEN.** Features with Variance Inflation Factor > 10 must be dropped or orthogonalized via PCA before inclusion.
- **Binary Sizing ONLY.** Position is always exactly 0.0 or 1.0. No fractional sizing. No "90% exposure."
- **No static in-sample fits.** All models must use Walk-Forward Optimization (WFO). No static train/test splits.
- **Piecewise normalization, not sigmoid.** Use linear interpolation against SD thresholds. Sigmoid over-smooths at extremes.
- **SQLite WAL for storage.** Zero-config, sufficient for single-machine pipeline. Do not introduce PostgreSQL/MySQL without explicit approval.
- **CausalFreshnessGuard on all data ingestion.** BRK data stamps must be validated: `stamp ≥ yesterday` or reject.

### Code Quality

- **One Component = One Script.** Each indicator pipeline is an isolated, independently backtestable script.
- **No hardcoded signals.** All thresholds are configurable via `metric_config` or parameter files.
- **No magic numbers.** All constants must be named and documented.
- **Type hints mandatory** (Python). All functions must have complete type annotations.
- **TypeScript strict mode** for all API and frontend code.
- **No `any` types** in TypeScript. Use proper interfaces.

---

## Git & Workflow Conventions

- **Branching Strategy:** `system/<name>/<task>` — e.g., `system/lttd/add-vif-pruning`, `system/valuation/migrate-schema`
- **Commit Format:** Conventional Commits with system prefix — e.g., `feat(lttd): add PCA orthogonalization`, `fix(ichimoku): correct tanh threshold`
- **Pushing Rules:** Never force push. Always rebase before merging.
- **PR Requirements:** All changes must pass tests, type checks, and lint. No direct pushes to `main`.
- **Documentation Updates:** When changing architecture, update `UNIFIED_SYSTEM_ARCHITECTURE.md` and relevant `docs/*.md`.

---

## Dependencies & Environment

### Python (Analytics Engines)

- Python 3.10+
- pandas 2.0+
- numpy
- scikit-learn 1.4+
- hmmlearn (Gaussian HMM)
- XGBoost
- scipy (statistical tests)
- sqlite3 (WAL mode)

### TypeScript/Bun (API + Frontend)

- Bun runtime
- Hono v4 (API framework)
- React 18 + TypeScript
- Vite (build tool)
- TradingView Lightweight Charts v5

### Data Sources

- **Binance API:** OHLCV daily (BTCUSDT)
- **bitview.space BRK API:** On-chain metrics (MVRV, NUPL, SOPR, Supply)
- **alternative.me:** Fear & Greed Index
- **yfinance:** BTC/USD backup

---

## Context Window Management

> Agents: This repository will grow. Stay within context limits.

1. **Read Gold Standard files first** before any deep work — not the whole repo.
2. **Use `module_report`** for structured file overviews instead of reading full files.
3. **Use `ast_grep_search`** for semantic code search — never raw grep for patterns.
4. **One system at a time.** Do not attempt to modify all 4 systems in a single session.
5. **Document decisions** in this file so future agents don't re-explore.

---

## Historical Session Learnings (Dynamic Log)

*When you consistently fail at a specific architectural nuance or encounter a repeating edge-case, add a note here to prevent future agents from making the same mistake.*

- **[2026-07-08]** This is a documentation-only repository — no code files exist yet. Code lives in separate repos: `quant-btc-valuation-system`, `quant-btc-lttd-system`, `quant-btc-mttd-system`, `quant-lttd-ichimoku`. (from initial setup)
- **[2026-07-08]** `quant-technical-indicator-bank` is EXCLUDED from this project — do not add references to it. (from user request)
- **[2026-07-08]** Always use `/session-learn` and `/daily-reflect` to evolve this file and record daily reflections. (from user request)

---

*Last updated: 2026-07-08*
*Maintainer: lutfi-zain*
