# Documentation Directory

**This directory contains project documentation separate from active project management.**

## 🎯 Purpose: Documentation vs Project Management

### What's Here (docs/)
- **Technical Documentation**: Architecture decisions, development guides
- **Generated Content**: Auto-created from GitHub Issues (future)
- **Permanent Records**: Compliance docs, technical specifications
- **Developer Resources**: Setup guides, workflows, standards

### What's NOT Here (moved to .github/)
- **Active Project Management**: Use [GitHub Issues](../.github/README.md) instead
- **Epic/Story Creation**: Use [Issue Templates](../../../issues/new/choose)
- **Status Tracking**: Monitor [GitHub Issues](../../../issues)

## 📁 Directory Structure

```
docs/
├── README.md                    # This guide
├── 01-business/                # 📋 DEPRECATED: Being phased out
│   └── README.md               # Points to GitHub Issues
├── 02-technical/               # 🔧 TECHNICAL: Architecture & guides
│   ├── bdd-scenarios/          # BDD test scenarios
│   ├── api-docs/               # API documentation
│   └── adrs/                   # Architecture Decision Records
├── 03-user/                    # 👤 USER: End-user documentation
│   └── guides/                 # User guides and help
├── generated/                  # 🤖 AUTO-GENERATED: From GitHub Issues
│   └── (future automation)    # RTM, status reports, summaries
└── traceability/               # 🔗 TRACEABILITY: Requirements tracking
    ├── requirements-matrix.md  # Links to GitHub Issues
    └── gdpr-compliance-map.md  # Privacy compliance mapping
```

## 🔄 Documentation Strategy

### GitHub-First Approach
1. **Create Issues**: Use [GitHub Issue Templates](../.github/ISSUE_TEMPLATE/)
2. **Track Work**: Monitor [GitHub Issues](../../../issues)
3. **Generate Docs**: Auto-create documentation from GitHub (future)
4. **Manual Docs**: Keep technical guides and decisions here

### Current Transition
- **Phase 1**: ✅ GitHub Issue templates active
- **Phase 2**: 🔄 Transitioning from docs/01-business/ to GitHub Issues
- **Phase 3**: 🔮 Auto-generation from GitHub Issues (US-010)

## 📖 Key Documentation

### For Active Development
- **[GitHub Issues](../../../issues)** - Current work and status
- **[Issue Templates](../../../issues/new/choose)** - Create new work
- **[CLAUDE.md](../CLAUDE.md)** - Development workflow and standards

### For Technical Reference
- **[Requirements Matrix](traceability/requirements-matrix.md)** - Full traceability
- **[BDD Scenarios](02-technical/bdd-scenarios/)** - Executable specifications
- **[Architecture Decisions](02-technical/adrs/)** - Technical decisions

### For Project Understanding
- **[Business Requirements](01-business/README.md)** - Overview (links to GitHub)
- **[GitHub Workflow](../.github/GITHUB_WORKFLOW.md)** - How project management works

## 🚫 What's Being Deprecated

### docs/01-business/ (Moving to GitHub)
- ~~epics/~~ → Use [GitHub Issues](../../../issues) with Epic template
- ~~user-stories/~~ → Use [GitHub Issues](../../../issues) with Story template
- ~~defects/~~ → Use [GitHub Issues](../../../issues) with Defect template

### Why the Change?
- **Single Source of Truth**: GitHub Issues are authoritative
- **Live Status**: Real-time updates vs static files
- **Better Collaboration**: Built-in discussions and assignments
- **Integrated Workflow**: Same platform as code and reviews

## 🤖 Future: Auto-Generated Documentation

**US-010** will implement automation to generate documentation from GitHub Issues:

```
GitHub Issues → Generated Documentation
├── Epic summaries
├── Updated RTM with live links
├── Status reports
├── Progress dashboards
└── Stakeholder summaries
```

## 🔗 Quick Navigation

### Primary (GitHub-based)
- **📋 Create Work**: [Issue Templates](../../../issues/new/choose)
- **📊 Track Progress**: [GitHub Issues](../../../issues)
- **🔧 Development**: [CLAUDE.md](../CLAUDE.md)

### Secondary (Documentation)
- **🔗 Traceability**: [Requirements Matrix](traceability/requirements-matrix.md)
- **⚙️ Technical**: [Technical Docs](02-technical/)
- **👤 User Guides**: [User Docs](03-user/)

---

**📌 Remember**: For all active project management, use [GitHub Issues](../../../issues). This documentation is for reference, technical specs, and generated content.