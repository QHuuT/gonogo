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

**Development and Quality Workflows (`docs/technical/`)**:
- Testing infrastructure changes (NEW)
- Quality gates modifications
- Development workflow updates
- Test reporting capabilities (NEW)

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
- Maintain clickable links to all referenced artifacts

**GDPR Compliance Map (`docs/traceability/gdpr-compliance-map.md`)**:
- Map features to GDPR requirements
- Track consent implementation
- Document data processing activities
- Link to technical implementation

## 🔄 Documentation Update Workflow

### **Daily Documentation Tasks (GitHub-First Protocol)**
1. **Check GitHub Issues**: Review new/updated issues for documentation needs
2. **UPDATE RTM IMMEDIATELY**: For every new GitHub issue created:
   - Add issue to RTM epic-to-user-story mapping
   - Update main RTM table with proper GitHub issue links
   - Set status to ⏳ In Progress when work begins
   - Add BDD scenario references when created
   - Update to ✅ Done when implementation complete
3. **Verify Links**: Ensure GitHub Issues reference relevant context docs
4. **Validate RTM Links**: Run `python tools/rtm-links-simple.py --validate` weekly

### **Feature Development Documentation (Enhanced Protocol)**
1. **Before Implementation**:
   - Create GitHub issue using templates (`gh issue create --template user-story`)
   - Review relevant ADRs in `docs/context/decisions/`
   - Check GDPR requirements in `docs/context/compliance/`
   - Verify BDD scenarios in `tests/bdd/features/`
   - **UPDATE RTM**: Add new issue to requirements matrix immediately

2. **During Implementation**:
   - **ADD BDD SCENARIOS TO GITHUB ISSUE**: Update issue description with scenario references
   - Update technical docs if architecture changes
   - Create/update BDD scenarios for new functionality
   - Document API changes in `docs/technical/api-docs/`
   - **UPDATE RTM STATUS**: Change to ⏳ In Progress

3. **After Implementation**:
   - **COMMENT ON GITHUB ISSUE**: Add implementation details and commit references
   - **UPDATE RTM**: Change status to ✅ Done with final implementation links
   - Verify GDPR compliance mapping
   - Update cross-references in documentation
   - **VALIDATE RTM**: Run RTM validation tool to ensure all links work

### **Major Decision Documentation**
1. **Create ADR**: New file in `docs/context/decisions/`
2. **Update GitHub Issues**: Reference ADR in relevant issues
3. **Update Technical Docs**: Implement ADR decisions in architecture docs
4. **Update DOCUMENTATION_MAP.md**: If workflow or project structure changes

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
- Epic EP-00007: Advanced Search Implementation
- User Story US-00015: Basic keyword search
- User Story US-00016: Filter by category

**Implementation Tracking**:
See [Requirements Matrix](../traceability/requirements-matrix.md) for current status.
```

## 🔍 Documentation Quality Checks

### **Before Every Commit**
- [ ] All new GitHub Issues linked in RTM
- [ ] Cross-references updated (GitHub Issues ↔ Documentation)
- [ ] GDPR implications documented if personal data involved
- [ ] Technical docs updated if architecture changed
- [ ] RTM links validated if traceability matrix changed

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

## 🔗 Requirements Traceability Matrix Link Management

### **RTM Link Types and Standards**

The RTM maintains clickable links to all referenced artifacts:

**Epic Links**:
- **Format**: `[**EP-XXXXX**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-XXXXX)`
- **Purpose**: Direct navigation to GitHub epic issues
- **Example**: `[**EP-00001**](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00001)`

**User Story Links**:
- **Format**: `[US-XXXXX](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+US-XXXXX)`
- **Purpose**: Direct navigation to GitHub user story issues
- **Example**: `[US-00014](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+US-00014)`

**BDD Scenario Links**:
- **Format**: `[feature-name.feature:scenario](../../tests/bdd/features/feature-name.feature)`
- **Purpose**: Direct navigation to BDD feature files in repository
- **Example**: `[rtm-automation.feature:link_generation](../../tests/bdd/features/rtm-automation.feature)`

**Test Implementation Links**:
- **Format**: `[test_steps.py](../../tests/bdd/step_definitions/test_steps.py)`
- **Purpose**: Direct navigation to test step definitions
- **Example**: `[test_rtm_link_generator_steps.py](../../tests/bdd/step_definitions/test_rtm_link_generator_steps.py)`

**GDPR Requirement Links**:
- **Format**: `[**GDPR-XXXXX**](../context/compliance/gdpr-requirements.md)`
- **Purpose**: Direct navigation to GDPR requirements documentation
- **Example**: `[**GDPR-00001**](../context/compliance/gdpr-requirements.md)`

### **Manual RTM Link Maintenance Process**

**When creating new GitHub issues**:
1. Create epic/user story using GitHub issue templates
2. Note the issue number GitHub assigns
3. Update RTM epic-to-user-story mapping table
4. Add detailed requirement row to main RTM table
5. Add user story to BDD scenario mapping section
6. Use proper link formats for all references

**When creating new BDD scenarios**:
1. Create feature file in `tests/bdd/features/`
2. Update RTM BDD Scenario column with correct feature:scenario format
3. Create corresponding step definition file
4. Update Test Implementation column with step definition link

**When files are moved or renamed**:
1. Update all RTM relative path links
2. Verify all links still resolve correctly
3. Test link navigation in GitHub and local markdown viewers

### **RTM Link Validation Checklist**

**MANDATORY RTM Update Checklist (Before Every Commit)**:
- [ ] **GitHub Issues**: All epic/US/DEF links use GitHub issue search format
- [ ] **Implementation Status**: Status updated (⏳ → ✅) for completed work
- [ ] **BDD Scenarios**: All scenario links point to existing feature files
- [ ] **Test Links**: All test implementation links point to existing step definition files
- [ ] **GDPR Links**: All GDPR requirement links point to correct documentation
- [ ] **Path Validation**: Relative paths calculated correctly from RTM file location
- [ ] **Link Validation**: Run `python tools/rtm-links-simple.py --validate`
- [ ] **GitHub Integration**: No broken links when viewed in GitHub web interface

**Weekly RTM link health check**:
- [ ] All GitHub issue links resolve to actual issues
- [ ] All file links point to existing files in repository
- [ ] All relative paths are accurate after any file moves
- [ ] BDD scenario names match actual scenario titles in feature files

## 🤖 RTM Automation (Future)

### **Planned RTM Automation** (EP-00005):
- **US-00015**: Automated RTM link generation and validation
- **US-00016**: GitHub Action for automated RTM validation
- **US-00017**: Comprehensive testing and extensibility framework

**Automation will**:
- Auto-generate all RTM links based on issue numbers and file paths
- Validate that all referenced files exist in repository
- Check that all GitHub issues are valid and accessible
- Create PRs with link updates when files are moved
- Report broken links as GitHub issues for manual resolution

### **Current Documentation Automation**:
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
- `docs/technical/development-workflow.md` - Development process with testing (UPDATED)
- `docs/technical/quality-assurance.md` - Code standards and test reporting (UPDATED)
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
