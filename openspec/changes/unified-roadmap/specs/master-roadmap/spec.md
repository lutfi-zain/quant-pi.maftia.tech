## ADDED Requirements

### Requirement: Master Roadmap Document

The system SHALL have a `ROADMAP.md` file at repository root that defines all implementation phases, milestones, dependencies, and success criteria.

#### Scenario: Roadmap file exists

- **WHEN** developer clones the repository
- **THEN** `ROADMAP.md` exists at root with 4 phases defined

#### Scenario: Roadmap has phases

- **WHEN** developer reads `ROADMAP.md`
- **THEN** file contains Phase 1 (Storage & ETL), Phase 2 (API Gateway), Phase 3 (Frontend Core), Phase 4 (Advanced Sandboxes)

#### Scenario: Roadmap has milestones

- **WHEN** developer reads any phase in `ROADMAP.md`
- **THEN** phase contains at least 3 milestones with clear deliverables

#### Scenario: Roadmap has dependencies

- **WHEN** developer reads `ROADMAP.md`
- **THEN** file shows phase dependencies (1 → 2 → 3 → 4)

### Requirement: Phase Status Tracking

The `ROADMAP.md` file SHALL include status indicators for each milestone.

#### Scenario: Milestone status

- **WHEN** developer reads a milestone
- **THEN** milestone has status: `[ ]` (not started), `[~]` (in progress), or `[x]` (complete)

### Requirement: OpenSpec Change Spawning

Each phase in the roadmap SHALL be implementable as a separate OpenSpec change.

#### Scenario: Phase can be proposed

- **WHEN** developer runs `/opsx:propose` for a phase
- **THEN** OpenSpec creates a change with phase-specific artifacts

#### Scenario: Phase has acceptance criteria

- **WHEN** developer reads a phase in `ROADMAP.md`
- **THEN** phase includes acceptance criteria that can be verified
