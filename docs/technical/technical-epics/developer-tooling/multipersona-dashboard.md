# EP-00010 - Multi-Persona Traceability Dashboard

**Epic Source**: [EP-00010 on GitHub](https://github.com/QHuuT/gonogo/issues/88)  
**Related Capability**: Strategic RTM Portfolio (capability `CAP-00002`)  
**Primary Stakeholders**: Project Manager, Product Owner, Quality Assurance

## Overview
The multi-persona traceability initiative replaces static RTM exports with role-specific, real-time dashboards. It consolidates dependency analysis, capability health, and quality metrics so that PM/PO/QA stakeholders can diagnose project risks rapidly.

Key deliverables from the epic include:
- Multi-persona dashboard shell (`src/be/templates/multipersona_dashboard.html`)
- Epic dependency visualizer (`src/be/api/epic_dependencies.py`, `src/be/templates/dependency_visualizer.html`)
- Capability portfolio view (`src/be/api/capabilities.py`, `src/be/templates/capability_portfolio.html`)
- Graph-generation utilities (`src/be/services/svg_graph_generator.py`)
- Data rework for epic metrics (`migrations/add_epic_metrics_columns.py`, `src/be/models/traceability/epic.py`)
- Test duplication audit tooling (`tools/audit_test_duplications.py`, `tools/advanced_duplicate_analysis.py`)

## Latest Progress (2025-09-25)
- Persona summary cards now pull schedule variance, velocity per member, and risk data returned by `src/be/api/rtm.py`.
- Charts for PM/PO/QA personas consume ROI, adoption, coverage, defect, and debt metrics from `src/be/templates/multipersona_dashboard.html`.
- User story `US-00072` moved to `in_review`; next focus is historical velocity feeds and automated regression tests.

## Regression Demo
- Curated dataset: `tests/demo/multipersona_dashboard_demo.json` defines three example epics with portfolio metrics.
- Automated check: `pytest tests/integration/rtm_api/test_dashboard_persona_demo.py` guards the summary contract for PM/PO/QA personas.
- Snapshot generator: `python tools/demo/prepare_dashboard_demo.py` writes `tools/demo/dashboard_persona_snapshot.json` for front-end smoke reviews.

## Traceability Snapshot
| User Story | GitHub | Status | Delivered Assets | Next Step |
| --- | --- | --- | --- | --- |
| US-00069 | [#89](https://github.com/QHuuT/gonogo/issues/89) | in_progress | Duplication audit scripts, CLI utilities in `tools/` | Run audit end-to-end, feed results into dashboard KPIs |
| US-00070 | [#90](https://github.com/QHuuT/gonogo/issues/90) | in_progress | Epic dependency ORM (`src/be/models/traceability/epic_dependency.py`) and API surface | Wire dependency graph data to dashboards, add regression tests |
| US-00071 | [#91](https://github.com/QHuuT/gonogo/issues/91) | in_progress | Epic metrics columns + model helpers | Calculate live metrics and expose them via dashboards |
| US-00072 | [#92](https://github.com/QHuuT/gonogo/issues/92) | in_review | Persona dashboards now render backend metrics (src/be/templates/multipersona_dashboard.html, src/be/api/rtm.py) | Add automated regression tests and velocity history feed |
| US-00073 | [#93](https://github.com/QHuuT/gonogo/issues/93) | in_progress | Dependency visualizer HTML/D3 shell | Connect REST data, add cycle/critical path overlays |
| US-00074 | [#94](https://github.com/QHuuT/gonogo/issues/94) | planned | Alerts workflow not yet implemented | Design alert rules + persistence, integrate with dashboards |
| US-00075 | [#95](https://github.com/QHuuT/gonogo/issues/95) | planned | Responsive layout pending | Define component layout tokens & CSS breakpoints |
| US-00076 | [#96](https://github.com/QHuuT/gonogo/issues/96) | planned | Obsolete assets still present | Catalogue removals and create cleanup migration |

> Database source: `gonogo.db` (`user_stories` table updated 2025-09-25)

## Architecture Notes
- **APIs**: `/api/epic-dependencies` (graph operations), `/api/capabilities` (program-level grouping), `/api/rtm/dashboard/*` routes for HTML dashboards.
- **Frontend**: Jinja2 templates + D3.js for dependency visualisation; CSS follows component-based design tokens in `static/css/`.
- **Data Pipeline**: SQLite dev database seeded from GitHub; duplication tools aggregate RTM test data prior to dashboard rendering.

## Testing & Quality
Current repository lacks targeted tests for the new dashboards and services.
- Add unit coverage for `svg_graph_generator` and dependency analytics helpers.
- Extend integration coverage under `tests/integration/rtm_api/` for new endpoints.
- Create BDD scenarios for persona dashboards (link to US-00072 acceptance criteria once defined).

## Open Risks
- **Data freshness**: duplication scripts need scheduled execution before dashboards rely on outputs.
- **Performance**: dependency graph queries should be benchmarked on larger datasets.
- **UX validation**: persona layouts require stakeholder sign-off; no automated visual regression exists yet.

## Immediate Next Steps
1. Finalise dependency graph data wiring (US-00070/US-00073) and add regression coverage for persona metrics (US-00072 follow-up).
2. Define alerting data model and notification surface (US-00074).
3. Build responsive layout utilities and finalize component inventory (US-00075).
4. Plan code cleanup to retire deprecated RTM assets (US-00076) once dashboards reach parity.


