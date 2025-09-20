# Documentation Workflow

**Last Updated**: 2025-09-20

## 🎯 Documentation Strategy Overview

Our documentation follows a **GitHub-First Approach** with stable context support:

- **GitHub Issues**: Active project management (EP-XXX, US-XXX, DEF-XXX)
- **Context Docs**: Stable decisions and compliance that GitHub Issues reference
- **Technical Docs**: Implementation guides and architecture
- **Living Docs**: Generated from GitHub Issues (future automation)

## 📂 When to Update Each Documentation Type

### **Context Documentation (`docs/context/`)**
Update when making **fundamental decisions** or **compliance changes**:

**Architecture Decisions (`docs/context/decisions/`)**:
- New ADR for major technology choices
- Business strategy changes
- Architecture pattern decisions
- GDPR approach modifications

**Compliance Requirements (`docs/context/compliance/`)**:
- GDPR requirement changes
- New legal obligations
- Privacy policy updates
- Data retention policy changes

### **Technical Documentation (`docs/technical/`)**
Update when **implementation details** change:

**System Architecture (`docs/technical/cross-cutting-architecture/`)**:
- New system components
- Integration pattern changes
- Security implementation updates
- Performance architecture changes

**BDD Scenarios (`tests/bdd/features/`)**:
- New feature scenarios
- Updated acceptance criteria
- GDPR compliance scenarios
- Security test scenarios

**API Documentation (`docs/technical/api-docs/`)**:
- New endpoints
- API contract changes
- Authentication updates
- Rate limiting changes

### **Traceability Documentation (`docs/traceability/`)**
Update **continuously** during development:

**Requirements Matrix (`docs/traceability/requirements-matrix.md`)**:
- Link GitHub Issues to implementation
- Track completion status
- Update test coverage
- Document defect relationships

**GDPR Compliance Map (`docs/traceability/gdpr-compliance-map.md`)**:
- Map features to GDPR requirements
- Track consent implementation
- Document data processing activities
- Link to technical implementation

## 🔄 Documentation Update Workflow

### **Daily Documentation Tasks**
1. **Check GitHub Issues**: Review new/updated issues for documentation needs
2. **Update RTM**: Link new GitHub Issues to requirements matrix
3. **Verify Links**: Ensure GitHub Issues reference relevant context docs

### **Feature Development Documentation**
1. **Before Implementation**:
   - Review relevant ADRs in `docs/context/decisions/`
   - Check GDPR requirements in `docs/context/compliance/`
   - Verify BDD scenarios in `tests/bdd/features/`

2. **During Implementation**:
   - Update technical docs if architecture changes
   - Create/update BDD scenarios for new functionality
   - Document API changes in `docs/technical/api-docs/`

3. **After Implementation**:
   - Update RTM with completion status
   - Verify GDPR compliance mapping
   - Update cross-references in documentation

### **Major Decision Documentation**
1. **Create ADR**: New file in `docs/context/decisions/`
2. **Update GitHub Issues**: Reference ADR in relevant issues
3. **Update Technical Docs**: Implement ADR decisions in architecture docs
4. **Update CLAUDE.md**: If workflow or project structure changes

## 📝 Documentation Cross-Reference Strategy

### **How GitHub Issues Reference Documentation**
```markdown
## Epic: EP-007 Advanced Search Implementation

**Context & Background**:
- Technology Choice: [ADR-001 Technology Stack](docs/context/decisions/adr-001-technology-stack.md)
- Privacy Requirements: [GDPR Requirements](docs/context/compliance/gdpr-requirements.md#data-minimization)

**Technical Implementation**:
- Architecture: [System Architecture](docs/technical/cross-cutting-architecture/system-architecture.md)
- Integration: [Integration Patterns](docs/technical/cross-cutting-architecture/integration-patterns.md)

**Testing**:
- BDD Scenarios: [Search Scenarios](tests/bdd/features/search-functionality.feature)
```

### **How Documentation References GitHub Issues**
```markdown
## ADR-003: Search Implementation Approach

**GitHub Issues Affected**:
- Epic EP-007: Advanced Search Implementation
- User Story US-015: Basic keyword search
- User Story US-016: Filter by category

**Implementation Tracking**:
See [Requirements Matrix](../traceability/requirements-matrix.md) for current status.
```

## 🔍 Documentation Quality Checks

### **Before Every Commit**
- [ ] All new GitHub Issues linked in RTM
- [ ] Cross-references updated (GitHub Issues ↔ Documentation)
- [ ] GDPR implications documented if personal data involved
- [ ] Technical docs updated if architecture changed

### **Weekly Documentation Review**
- [ ] Review RTM for broken links
- [ ] Verify GitHub Issues reference correct documentation
- [ ] Check for outdated ADRs or compliance docs
- [ ] Update any stale cross-references

### **Monthly Documentation Audit**
- [ ] Full link validation across all documentation
- [ ] Review ADRs for continued relevance
- [ ] Verify GDPR compliance documentation is current
- [ ] Update documentation structure if needed

## 🤖 Future Documentation Automation

**Planned automation** will:
- Auto-update RTM from GitHub Issues
- Generate progress reports from GitHub data
- Validate cross-references between docs and GitHub
- Create stakeholder summaries from active issues

## 🔗 Documentation Quick Reference

### **Context & Decisions**
- `docs/context/decisions/` - Architecture Decision Records
- `docs/context/compliance/` - GDPR and legal requirements

### **Technical Implementation**
- `docs/technical/cross-cutting-architecture/` - System architecture
- `tests/bdd/features/` - Executable test scenarios
- `docs/technical/api-docs/` - API documentation

### **Active Tracking**
- `docs/traceability/requirements-matrix.md` - GitHub Issues → Implementation
- `docs/traceability/gdpr-compliance-map.md` - Features → GDPR compliance

### **GitHub Integration**
- GitHub Issues reference stable documentation for context
- Documentation links to GitHub Issues for active work
- RTM provides bidirectional traceability

---

**Related Documentation**:
- [Development Workflow](development-workflow.md) - Complete development process
- [Context Documentation](../context/) - Stable decisions and compliance
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current traceability