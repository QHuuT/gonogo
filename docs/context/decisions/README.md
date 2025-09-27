# Architectural Decision Records (ADRs)

**Last Updated**: 2025-09-27

## 📋 Purpose

This directory contains **Architectural Decision Records** that document important business and technical decisions made during the development of GoNoGo. These provide context and rationale for future development and help maintain consistency.

## 🏗️ ADR Format

Each ADR follows a standard format:
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Date**: When the decision was made
- **Context**: Why a decision was needed
- **Decision**: What was decided
- **Consequences**: Positive and negative impacts
- **Implementation**: How it affects development

## 📚 Current ADRs

### Business & Architecture Decisions
- [**ADR-001: Technology Stack Selection**](adr-001-technology-stack-selection.md)
  - FastAPI, PostgreSQL, DigitalOcean EU hosting
  - Status: ✅ Accepted
  - Impact: All development follows this stack

- [**ADR-002: GDPR-First Architecture**](adr-002-gdpr-first-architecture.md)
  - Privacy-by-design principles and implementation
  - Status: ✅ Accepted
  - Impact: All features must implement privacy controls

- [**ADR-003: Hybrid GitHub + Database RTM Architecture**](adr-003-hybrid-github-database-rtm-architecture.md)
  - Database-driven RTM with GitHub integration
  - Status: ✅ Accepted
  - Impact: RTM data management and reporting

- [**ADR-004: Context-Aware Code Standards**](adr-004-context-aware-code-standards.md)
  - Graduated line length standards by code context
  - Status: ✅ Accepted
  - Impact: Different formatting rules for production vs test vs utility code

### Future ADRs (As Needed)
- **ADR-005**: Data Anonymization Techniques
- **ADR-006**: International Data Transfer Policies
- **ADR-007**: Performance Monitoring Strategy
- **ADR-008**: Content Moderation Approach

## 🔗 Relationship to GitHub Issues

### How GitHub Issues Reference ADRs
GitHub Issues should reference relevant ADRs for context:

```markdown
## Epic: EP-007 Advanced Search Implementation

**Context**: This epic implements search functionality while maintaining our privacy-first approach.

**Related ADRs**:
- ADR-001: Technology stack (FastAPI + PostgreSQL search)
- ADR-002: GDPR compliance (search query anonymization)

**Privacy Considerations**:
- Search queries will not be logged with user identifiers
- Search results filtered based on user consent levels
```

### When to Create New ADRs
Create a new ADR when making decisions about:
- **Architecture**: Major technical or business architecture changes
- **Technology**: Adding new technologies or changing existing ones
- **Privacy**: New approaches to GDPR compliance or data protection
- **Business Rules**: Fundamental changes to business logic or policies
- **Integration**: New external service integrations or patterns

## 📝 ADR Lifecycle

### 1. Proposed
- Decision needs to be made
- ADR draft created for discussion
- GitHub Issue created for decision discussion

### 2. Accepted
- Decision made and documented
- Implementation begins
- All related GitHub Issues reference the ADR

### 3. Deprecated/Superseded
- Decision no longer valid
- New ADR created if replacement needed
- Historical context preserved

## 🎯 Writing Good ADRs

### Include
- **Clear context**: Why was this decision needed?
- **Specific decision**: What exactly was decided?
- **Alternatives considered**: What other options were evaluated?
- **Implementation impact**: How does this affect development?
- **Success metrics**: How will we know if this was the right decision?

### Avoid
- **Technical details**: Keep focus on decisions, not implementation
- **Implementation instructions**: ADRs explain why, not how
- **Changing decisions**: Create new ADRs instead of editing old ones

## 🔄 Review Process

### Regular Review
- **Quarterly**: Review all accepted ADRs for continued relevance
- **Major features**: Check if existing ADRs need updates or new ones needed
- **Technology changes**: Assess if stack changes require new ADRs

### Update Process
1. **Never edit accepted ADRs**: They are historical records
2. **Create new ADRs**: To supersede or update previous decisions
3. **Link related ADRs**: Show decision evolution over time
4. **Update GitHub Issues**: Reference new ADRs in relevant issues

---

**GitHub Integration**: ADRs provide stable context that GitHub Issues can reference
**Technical Details**: For implementation specifics, see docs/02-technical/
**Business Context**: For business requirements, see docs/01-business/requirements/