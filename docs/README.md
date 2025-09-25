# Documentation Directory

**This directory contains project documentation separate from active project management.**

## 🎯 Purpose: Documentation vs Project Management

### What's Here (docs/)
- **Context Documentation**: Stable decisions and compliance requirements
- **Technical Documentation**: Architecture, implementation guides, and specifications
- **User Documentation**: End-user guides and help content
- **Traceability**: Requirements tracking and compliance mapping

### What's NOT Here (moved to .github/)
- **Active Project Management**: Use [GitHub Issues](../.github/README.md) instead
- **Epic/Story Creation**: Use [Issue Templates](../../../issues/new/choose)
- **Status Tracking**: Monitor [GitHub Issues](../../../issues)

## 📁 Directory Structure

```
docs/
├── README.md                    # This guide
├── context/                     # 🎯 CONTEXT: Stable decisions & compliance
│   ├── decisions/              #   📋 ADRs (architecture decisions)
│   └── compliance/             #   ⚖️  GDPR and legal requirements
├── technical/                   # 🔧 TECHNICAL: Implementation docs
│   ├── cross-cutting-architecture/  #   🏗️  System architecture
│   ├── bdd-scenarios/          #   🧪 BDD test scenarios
│   ├── api-docs/               #   📡 API documentation
│   └── technical-epics/        #   📋 Technical implementation guides
├── user/                        # 👤 USER: End-user documentation
│   └── guides/                 #   📖 User guides and help
├── traceability/               # 🔗 TRACEABILITY: Requirements tracking
│   ├── requirements-matrix.md  #   📊 DEPRECATED - See database RTM
│   └── gdpr-compliance-map.md  #   🛡️  Privacy compliance mapping
└── generated/                  # 🤖 AUTO-GENERATED: From GitHub Issues
    └── (future automation)    #   📈 RTM, status reports, summaries
```

## 🔄 Documentation Strategy

### GitHub-First Approach
1. **Create Issues**: Use [GitHub Issue Templates](../.github/ISSUE_TEMPLATE/)
2. **Track Work**: Monitor [GitHub Issues](../../../issues)
3. **Reference Context**: Link to stable docs for background
4. **Generate Reports**: Auto-create summaries from GitHub (future)

### Documentation Types
- **Context Docs**: Stable background (ADRs, compliance) that GitHub Issues reference
- **Technical Docs**: Implementation details and architecture
- **Living Docs**: Generated from GitHub Issues (future automation)

## 📖 Key Documentation

### For Active Development
- **[GitHub Issues](../../../issues)** - Current work and status
- **[Issue Templates](../../../issues/new/choose)** - Create new work
- **[Development Workflow](technical/development-workflow.md)** - Day-to-day engineering process and standards

### For Context & Background
- **[Context Documentation](context/)** - Stable decisions and compliance
  - [Architecture Decisions](context/decisions/) - Major technical and business decisions
  - [GDPR Requirements](context/compliance/gdpr-requirements.md) - Privacy compliance
- **[RTM Web Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html)** - Interactive requirements traceability

### For Technical Reference
- **[Technical Documentation](technical/)** - Implementation and architecture
  - [System Architecture](technical/cross-cutting-architecture/system-architecture.md) - Overall system design
  - [Security Architecture](technical/cross-cutting-architecture/security-architecture.md) - Security and GDPR implementation
  - [Integration Patterns](technical/cross-cutting-architecture/integration-patterns.md) - Service communication patterns
  - [BDD Scenarios](technical/bdd-scenarios/) - Executable specifications
  - [Multi-Persona Traceability Dashboard](technical/technical-epics/developer-tooling/multipersona-dashboard.md) - Epic EP-00010 implementation status

### For End Users
- **[User Documentation](user/)** - End-user guides and help

## 🔗 How GitHub Issues Reference Documentation

### Example GitHub Issue Structure
```markdown
## Epic: EP-007 Advanced Search Implementation

**Context & Background**:
- Technology Choice: [ADR-001 Technology Stack](docs/context/decisions/adr-001-technology-stack.md)
- Privacy Requirements: [GDPR Requirements](docs/context/compliance/gdpr-requirements.md#data-minimization)

**Technical Implementation**:
- Architecture: [System Architecture](docs/technical/cross-cutting-architecture/system-architecture.md)
- Integration: [Integration Patterns](docs/technical/cross-cutting-architecture/integration-patterns.md)

**Testing**:
- BDD Scenarios: [Search Scenarios](docs/technical/bdd-scenarios/search-functionality.feature)
```

## 🤖 Future: Auto-Generated Documentation

**Planned automation** will generate documentation from GitHub Issues:

```
GitHub Issues → Generated Documentation
├── Epic summaries and progress reports
├── Updated RTM with live GitHub links
├── Status dashboards and metrics
├── Stakeholder summaries
└── Compliance tracking reports
```

## 🔗 Quick Navigation

### Primary (GitHub-based)
- **📋 Create Work**: [Issue Templates](../../../issues/new/choose)
- **📊 Track Progress**: [GitHub Issues](../../../issues)
- **🔧 Development**: [technical/development-workflow.md](technical/development-workflow.md)

### Context & Background
- **🎯 Decisions**: [Architecture Decisions](context/decisions/)
- **⚖️ Compliance**: [GDPR Requirements](context/compliance/gdpr-requirements.md)
- **🔗 Traceability**: [RTM Web Dashboard](http://localhost:8000/api/rtm/reports/matrix?format=html) or [RTM Guide](../quality/RTM_GUIDE.md)

### Technical Implementation
- **🏗️ Architecture**: [Cross-Cutting Architecture](technical/cross-cutting-architecture/)
- **📡 APIs**: [API Documentation](technical/api-docs/)
- **🧪 Testing**: [BDD Scenarios](technical/bdd-scenarios/)

### User Support
- **👤 User Guides**: [User Documentation](user/)

---

**📌 Remember**: For all active project management, use [GitHub Issues](../../../issues). This documentation provides stable context and technical reference that GitHub Issues can link to for background information.