## ADDED Requirements

### Requirement: React + Vite + TypeScript Scaffold

The system SHALL have a React 18 + Vite + TypeScript frontend application.

#### Scenario: Dev server starts

- **WHEN** developer runs `bun run dev`
- **THEN** Vite dev server starts on port 5173

#### Scenario: TypeScript strict mode

- **WHEN** developer runs `bun run typecheck`
- **THEN** no TypeScript errors with strict mode enabled

### Requirement: Design Token System

The frontend SHALL use HSL CSS variables for theming.

#### Scenario: CSS variables defined

- **WHEN** developer inspects `:root` in CSS
- **THEN** variables include `--deep-obsidian`, `--bull-emerald`, `--neutral-amber`, `--bear-crimson`

#### Scenario: Glassmorphism panels

- **WHEN** developer renders `.glass-panel` component
- **THEN** panel has `backdrop-filter: blur(12px)` and translucent background

### Requirement: Executive Dashboard Layout

The frontend SHALL display an Executive Dashboard with Bento grid layout.

#### Scenario: Dashboard renders

- **WHEN** user navigates to root URL
- **THEN** Executive Dashboard loads with Cross-System Confluence Gauge, Action Banner, and Summary Table

#### Scenario: Bento grid structure

- **WHEN** dashboard loads
- **THEN** layout uses CSS Grid with responsive columns

### Requirement: Cross-System Confluence Gauge

The frontend SHALL display a radial gauge showing system agreement.

#### Scenario: Gauge renders

- **WHEN** dashboard loads
- **THEN** Confluence Gauge shows percentage (0-100%) of system agreement

#### Scenario: Gauge updates

- **WHEN** API returns new consensus data
- **THEN** gauge animates to new percentage value

### Requirement: Action Banner

The frontend SHALL display an Action Banner showing current position status.

#### Scenario: Circuit breaker banner

- **WHEN** MVO ≥ +1.50
- **THEN** banner displays "🔴 CIRCUIT BREAKER ACTIVE — ALL SYSTEMS HALTED" in crimson

#### Scenario: Bear regime banner

- **WHEN** LTTD regime is BEAR
- **THEN** banner displays "🟡 BEAR REGIME — ALL EXPOSURE HALTED" in amber

#### Scenario: Normal mode banner

- **WHEN** no safeguards active
- **THEN** banner displays current exposure status

### Requirement: Interactive Summary Table

The frontend SHALL display a sortable table with per-system status.

#### Scenario: Table renders

- **WHEN** dashboard loads
- **THEN** table shows Valuation, LTTD, MTTD, and Ichimoku rows with Score, Position, and Gate Status columns

#### Scenario: Table sortable

- **WHEN** user clicks column header
- **THEN** table sorts by that column

### Requirement: BTC Price Chart with Overlay

The frontend SHALL display a BTC price chart with system overlays.

#### Scenario: Price chart renders

- **WHEN** dashboard loads
- **THEN** TradingView Lightweight Charts renders BTC/USD candlestick chart

#### Scenario: Regime overlay

- **WHEN** LTTD regime data available
- **THEN** chart displays regime bands (green=BULL, red=BEAR, gray=SIDEWAYS)

### Requirement: Vertical Crosshair Synchronization

The frontend SHALL synchronize crosshair position across all charts.

#### Scenario: Crosshair sync

- **WHEN** user moves mouse on BTC price chart
- **THEN** all other charts update their crosshair to same time position

### Requirement: 85px Y-Axis Width Lock

The frontend SHALL lock all right-side price axes to 85px width.

#### Scenario: Y-axis alignment

- **WHEN** multiple charts are stacked vertically
- **THEN** all right-side price axes have exactly 85px width
- **THEN** horizontal grid lines align across all charts
