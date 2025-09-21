# ADR-008: Hybrid GitHub + Database RTM Architecture

**Date**: 2025-09-20
**Status**: Accepted
**Deciders**: Project Team
**Context**: Database-driven RTM migration planning

## Context

The current Requirements Traceability Matrix (RTM) system uses static markdown files managed manually. As part of EP-00005 (RTM Automation), we need to decide on the target architecture for a database-driven RTM system that improves automation, reporting, and relationship management while maintaining developer workflow efficiency.

## Decision

We will implement a **hybrid architecture** that leverages both GitHub Issues and a database system:

### GitHub Managed Entities
- **User Stories (US-XXXXX)**: Continue using GitHub Issues for workflow, discussion, assignment, and status tracking
- **Defects (DEF-XXXXX)**: Continue using GitHub Issues for bug tracking, resolution, and collaboration

### Database Managed Entities
- **Epics (EP-XXXXX)**: Migrate to database for better relationship management and progress calculation
- **Tests**: Store in database with execution results, BDD scenario links, and traceability chains
- **Visualization & Reporting**: Database-powered dashboards, RTM generation, and analytics

## Rationale

### Advantages of Hybrid Approach

#### Leverages GitHub Strengths
- **Workflow Integration**: Issues integrate naturally with pull requests, code review, and developer workflow
- **Collaboration**: Rich commenting, assignment, labeling, and notification systems
- **Ecosystem**: Existing tools, integrations, and team familiarity
- **Version Control**: Issue history and audit trail built into GitHub

#### Leverages Database Strengths
- **Complex Relationships**: Proper foreign keys and referential integrity for Epic → US → Test chains
- **Real-time Reporting**: Dynamic progress calculation and completion percentages
- **Advanced Queries**: Complex filtering, aggregation, and analytical queries
- **Performance**: Fast queries for dashboard and visualization needs

#### Simplified Migration
- **No GitHub Issue Migration**: Existing US/DEF issues remain in GitHub unchanged
- **Reduced Complexity**: Avoid complex GitHub API synchronization for all entity types
- **Incremental Rollout**: Can migrate Epics and Tests independently
- **Rollback Safety**: GitHub issues remain accessible if database migration fails

### Technical Benefits

#### Data Synchronization
- **Unidirectional Sync**: GitHub → Database for US/DEF metadata (simpler than bidirectional)
- **Reference-based Linking**: US/DEF issues reference Epic IDs for database lookups
- **Event-driven Updates**: GitHub webhooks trigger database updates when issues change

#### Reporting & Analytics
- **Epic Progress**: Calculated from linked GitHub US/DEF completion status
- **Test Coverage**: Database queries across Epic → US → Test relationships
- **Dynamic RTM**: Real-time generation from hybrid data sources
- **Historical Tracking**: Database stores test execution history and trends

#### Developer Experience
- **Familiar Workflow**: Continue using GitHub for day-to-day US/DEF management
- **Enhanced Visibility**: Rich dashboards and reports for epic progress and test status
- **Reduced Friction**: No workflow changes for issue creation and management

## Alternatives Considered

### Full GitHub Migration
**Rejected**: GitHub Issues lack advanced relationship management, complex queries, and real-time reporting capabilities needed for comprehensive RTM automation.

### Full Database Migration
**Rejected**: Would require migrating existing issues, losing GitHub workflow integration, and building UI for issue management.

### Static File Enhancement
**Rejected**: Doesn't solve fundamental problems with manual maintenance, relationship management, and dynamic reporting.

## Implementation Implications

### Database Schema
```sql
-- Epics stored in database
Epics: id, title, description, status, github_reference_id

-- Tests stored in database
Tests: id, epic_id(FK), github_us_reference, github_def_reference,
       test_file_path, bdd_scenario, execution_status

-- US/DEF remain in GitHub with Epic references in issue body
```

### GitHub Integration
- GitHub Actions parse Epic references from US/DEF issue bodies
- Database stores GitHub issue metadata (title, status, labels)
- Epic progress calculated from linked GitHub issue status

### Visualization
- Web dashboard queries database for Epic/Test data
- Dashboard fetches GitHub issue metadata via API for US/DEF details
- Combined reporting from both data sources

## Consequences

### Positive
- **Best of Both Worlds**: GitHub workflow + Database analytics
- **Incremental Migration**: Lower risk, gradual rollout possible
- **Performance**: Database queries for complex reporting
- **Maintainability**: Clear separation of concerns

### Negative
- **Dual System Complexity**: Must maintain sync between GitHub and database
- **Data Consistency**: Risk of GitHub ↔ Database inconsistencies
- **Development Overhead**: Must consider both systems in feature development

### Mitigation Strategies
- **Robust Sync Mechanisms**: Event-driven updates with retry logic
- **Monitoring**: Database consistency checks and alerting
- **Documentation**: Clear guidelines for when to use GitHub vs database
- **Testing**: Comprehensive integration tests for sync mechanisms

## Compliance Considerations

### GDPR
- **Personal Data**: GitHub handles user assignments and comments (existing GDPR compliance)
- **Database Storage**: Epic and test data contains no personal information
- **Data Retention**: Align database retention with GitHub issue lifecycle

### Security
- **GitHub Access**: Leverage existing GitHub authentication and authorization
- **Database Security**: Standard database security practices and access controls
- **API Security**: Secure GitHub webhook endpoints and database API access

## Success Metrics

- **Epic Progress Accuracy**: Real-time calculation from GitHub issue status
- **RTM Generation Speed**: < 5 seconds for full RTM report generation
- **Data Consistency**: > 99.9% sync accuracy between GitHub and database
- **Developer Adoption**: No workflow disruption for US/DEF management

## Related ADRs

- **ADR-001**: FastAPI + SQLAlchemy architecture (database foundation)
- **ADR-002**: GitHub-first development workflow (GitHub integration)
- **ADR-005**: Test logging and reporting system (test data foundation)

## Implementation Timeline

- **Phase 1**: Database schema design and Epic migration (US-00052, US-00054)
- **Phase 2**: GitHub sync integration (US-00053, US-00056)
- **Phase 3**: Test integration and visualization (US-00057, US-00059)
- **Phase 4**: Documentation and migration completion (US-00058, US-00060)