# 🤖 Maftia Quant — AI Agent Handoff Prompt

> **Repository:** `quant-pi.maftia.tech`  
> **Date:** 2026-07-08  
> **Purpose:** Comprehensive handoff document for AI agents to understand the Maftia Quant Bitcoin Intelligence Platform architecture, execute tasks, and continue development.

---

## 1. What Is This Repository?

This is the **central documentation and architecture repository** for the Maftia Quant platform — a unified quantitative Bitcoin intelligence system that aggregates 4 independent trading systems and 1 indicator bank into a cohesive intelligence platform with interlocking safeguards.

---

## 2. The 5 Component Systems

| # | System | Purpose | Horizon | Key Method |
|---|--------|---------|---------|------------|
| 1 | **Valuation System** | Macro cycle peak/trough detection | Multi-year | 17-indicator MVO, piecewise [-2,+2] |
| 2 | **LTTD System** | Long-term trend direction | 120–350 days | 3-State HMM + PCA + XGBoost |
| 3 | **MTTD System** | Medium-term trend following | 10–120 days | Multi-principle consensus + IMO |
| 4 | **Ichimoku Terminal** | Denoised Ichimoku signals | 10–60 days | tanh normalization + SuperSmoother |
| 5 | **Indicator Bank** | Pine→Python indicator library | Library | 10 statistical families |

---

## 3. The Interlocking Matrix

**This is the most important architectural concept.**

Systems do not operate independently. The output of one system constrains the behavior of another:

1. **Circuit Breaker:** Valuation MVO ≥ +1.50 → ALL systems forced to 0.0 exposure
2. **Regime Override:** LTTD BEAR/SIDEWAYS → MTTD & Ichimoku forced to 0.0 exposure
3. **Consensus Aggregation:** Final exposure = intersection of all constraints

---

## 4. Data Flow

```
Binance OHLCV + bitview.space BRK + alternative.me
        ↓
    maftia_quant.db (SQLite WAL)
        ↓
    Valuation → LTTD → MTTD → Ichimoku → Indicator Bank
        ↓
    api.quant-pi.maftia.tech (Hono v4 / Bun)
        ↓
    Executive Dashboard + 5 Sandboxes
```

---

## 5. Key Files

| File | Description |
|------|-------------|
| `UNIFIED_SYSTEM_ARCHITECTURE.md` | Master architecture document — read this first |
| `README.md` | Project index and Mermaid interlocking diagram |
| `docs/01_quant_btc_valuation_system.md` | Valuation System deep-dive |
| `docs/02_quant_btc_lttd_system.md` | LTTD System deep-dive |
| `docs/03_quant_btc_mttd_system.md` | MTTD System deep-dive |
| `docs/04_quant_lttd_ichimoku.md` | Ichimoku Terminal deep-dive |
| `docs/05_quant_technical_indicator_bank.md` | Indicator Bank deep-dive |
| `PROMPT_HANDOFF.md` | This document |

---

## 6. Critical Concepts

- **CausalFilter:** Every indicator uses only past bars — zero lookahead bias
- **OU Half-Life:** Bitcoin's structural reversion speed (120–350 days post-2020)
- **PCA Orthogonalization:** Eliminates multicollinearity before ensemble aggregation
- **tanh Normalization:** Converts non-stationary Ichimoku to stationary [-1, +1] oscillators
- **Kaufman ER Gate:** Blocks entries during random walk / consolidation
- **Shannon Entropy Gate:** Blocks entries during chaotic regimes
- **Walk-Forward Optimization:** No static in-sample fit — rolling train/validate/test

---

## 7. Current Market Status (2026-07-08)

| System | Score | Position | Status |
|--------|-------|----------|--------|
| Valuation | +1.52 | — | High (historical deep discount) |
| LTTD | -0.44 | 0.0 | BEAR regime |
| MTTD | -0.99 | 0.0 | IMO blocked |
| Ichimoku | -0.99 | 0.0 | Neutral |
| **Consensus** | — | **0.0** | **100% Cash / Neutral Mode** |

---

## 8. How to Continue Development

1. Read `UNIFIED_SYSTEM_ARCHITECTURE.md` for the master plan
2. Read the relevant `docs/*.md` for system-specific details
3. Follow the 4-phase roadmap in Section 9 of UNIFIED_SYSTEM_ARCHITECTURE.md
4. All interlocking safeguards must be preserved — never bypass circuit breakers
5. All indicators must use CausalFilter — never introduce lookahead bias
6. All new indicators must pass VIF < 10 before inclusion

---

*"The map is not the territory. The model is not the market. But a good map prevents you from walking off a cliff."*
