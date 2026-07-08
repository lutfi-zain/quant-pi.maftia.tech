## ADDED Requirements

### Requirement: Sandbox Framework

The system SHALL have a sandbox framework for deep-dive workspaces.

#### Scenario: Sandbox navigation

- **WHEN** user clicks sandbox link in dashboard
- **THEN** application navigates to full-screen sandbox view

#### Scenario: Sandbox layout

- **WHEN** sandbox loads
- **THEN** layout displays system-specific panels and charts

### Requirement: Valuation Pillar Studio

The system SHALL have a Valuation Pillar Studio sandbox.

#### Scenario: Three-pillar display

- **WHEN** user opens Valuation Studio
- **THEN** display shows Fundamental, Technical, and Sentiment pillars with indicator lists

#### Scenario: Master oscillator chart

- **WHEN** Valuation Studio loads
- **THEN** chart displays MVO score time-series with threshold lines

#### Scenario: Threshold editor

- **WHEN** user drags threshold line on chart
- **THEN** score recalculates in real-time

### Requirement: LTTD Orthogonal Regime Lab

The system SHALL have an LTTD Regime Lab sandbox.

#### Scenario: Regime timeline

- **WHEN** user opens LTTD Lab
- **THEN** chart displays historical regime states (BULL/BEAR/SIDEWAYS) as colored bands

#### Scenario: PCA visualization

- **WHEN** LTTD Lab loads
- **THEN** display shows PCA component loadings and variance explained

#### Scenario: VIF heatmap

- **WHEN** LTTD Lab loads
- **THEN** display shows indicator correlation matrix with VIF values

#### Scenario: WFO fold results

- **WHEN** LTTD Lab loads
- **THEN** table shows train/val/test Sharpe ratio per WFO fold

### Requirement: MTTD Console

The system SHALL have an MTTD Console sandbox.

#### Scenario: IMO time-series

- **WHEN** user opens MTTD Console
- **THEN** chart displays IMO score with gate annotations

#### Scenario: Trade markers

- **WHEN** MTTD Console loads
- **THEN** chart displays entry/exit markers on price chart

#### Scenario: Gate blocker heatmap

- **WHEN** MTTD Console loads
- **THEN** display shows which gate blocked entries and when

### Requirement: Ichimoku Terminal

The system SHALL have an Ichimoku Terminal sandbox.

#### Scenario: 4-component breakdown

- **WHEN** user opens Ichimoku Terminal
- **THEN** display shows S_TK, S_Cloud, S_Future, S_Chikou scores

#### Scenario: Cloud overlay

- **WHEN** Ichimoku Terminal loads
- **THEN** chart displays tanh-normalized Ichimoku cloud overlay on BTC price

#### Scenario: SuperSmoother tuner

- **WHEN** Ichimoku Terminal loads
- **THEN** display shows sliders for SuperSmoother parameters (l=4, l=7)

#### Scenario: Statistical test results

- **WHEN** Ichimoku Terminal loads
- **THEN** panel displays ADF, KS, t-test, Bootstrap, and Bonferroni results
