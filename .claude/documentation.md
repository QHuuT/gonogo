# 📚 Documentation Agent

**Purpose**: Documentation creation, updates, maintenance, and cross-reference management

## 📖 Documentation Overview

### **Documentation Structure**
```
docs/
├── context/                    # Stable decisions & compliance
│   ├── decisions/             # Architecture Decision Records (ADRs)
│   └── compliance/            # GDPR and legal requirements
├── technical/                 # Technical implementation docs
│   ├── development-workflow.md     # Complete development process
│   ├── documentation-workflow.md  # Documentation maintenance
│   ├── quality-assurance.md       # Code standards and quality
│   └── cross-cutting-architecture/  # System architecture
├── user/                      # End-user documentation
└── traceability/              # Requirements tracking (deprecated - use database RTM)

quality/
├── README.md                  # Quality reports guide
├── RTM_GUIDE.md              # RTM dashboard documentation
├── TESTING_GUIDE.md          # Testing workflows
└── QUICK_REFERENCE.md        # Quality thresholds
```

## 📝 Documentation Workflows

### **Creating New Documentation**
```bash
# Before creating documentation
1. Check existing docs to avoid duplication
2. Determine appropriate location (docs/ vs quality/)
3. Follow naming conventions (kebab-case.md)
4. Use standard templates and structure

# Documentation creation checklist
- [ ] Clear purpose and audience defined
- [ ] Consistent formatting and style
- [ ] Code examples tested and working
- [ ] Cross-references added where relevant
- [ ] RTM links updated if applicable
```

### **Updating Existing Documentation**
```bash
# Documentation update workflow
1. Read entire document for context
2. Update specific sections without breaking flow
3. Validate all code examples still work
4. Update "Last Updated" dates
5. Check and fix any broken cross-references

# Cross-reference validation
python tools/rtm-links.py validate                    # Validate RTM links (legacy)
# Manual check: Verify all [](file.md) links work
# Manual check: Ensure all referenced files exist
```

## 🔗 RTM Documentation Management

### **Database RTM Documentation**
```bash
# RTM database documentation commands
python tools/rtm-db.py --help                        # Full CLI documentation
python tools/rtm-db.py query epics --format table    # Document epic status
python tools/rtm-db.py admin health-check            # Document system health

# RTM web dashboard documentation
# Start server: python -m uvicorn src.be.main:app --reload
# Document URL: http://localhost:8000/api/rtm/reports/matrix?format=html

# RTM report generation documentation
python tools/rtm_report_generator.py --html          # Generate documented reports
python tools/rtm_demo.py --html                      # Generate demo documentation
```

### **RTM Documentation Structure**
- **quality/RTM_GUIDE.md**: Complete user guide for RTM dashboard
- **quality/TESTING_GUIDE.md**: Testing workflows with RTM integration
- **docs/technical/rtm-migration-validation.md**: Migration documentation
- **CLAUDE.md**: Agent navigation and essential RTM commands

### **GitHub Integration Documentation**
```bash
# Document GitHub issue workflows
gh issue view 123                                    # Document issue details
gh project list                                     # Document project structure

# GitHub sync documentation
python tools/github_sync_manager.py --help          # Document sync options
python tools/github_sync_manager.py --dry-run       # Document sync process
```

## 📋 Documentation Standards

### **Style Guide**
- **Headers**: Use `# ## ### ####` hierarchy consistently
- **Code Blocks**: Use ` ```bash ` with descriptive language tags
- **Links**: Use `[Text](path/to/file.md)` format
- **Emphasis**: Use `**bold**` for important terms, `*italic*` for emphasis
- **Lists**: Use `-` for unordered, `1.` for ordered lists
- **Emojis**: Use sparingly for section headers (🎯 📚 🔧 etc.)

### **Content Standards**
- **Purpose Statement**: Every document starts with clear purpose
- **Audience**: Define who the documentation is for
- **Prerequisites**: List required knowledge/setup
- **Examples**: Provide working code examples
- **Troubleshooting**: Include common issues and solutions
- **Cross-References**: Link to related documentation

### **Technical Writing Guidelines**
```markdown
# Good Example
## Database Migration

**Purpose**: Migrate user data while maintaining GDPR compliance

**Prerequisites**:
- Database backup completed
- Migration scripts tested

**Steps**:
1. Stop application server
2. Run migration: `alembic upgrade head`
3. Validate data integrity
4. Restart application

**Troubleshooting**:
- If migration fails: restore from backup
- If data missing: check migration logs
```

## 🔄 Documentation Maintenance

### **Regular Maintenance Tasks**
```bash
# Weekly documentation maintenance
1. Check for broken links in key documents
2. Validate code examples still work
3. Update "Last Updated" dates for changed files
4. Review and update cross-references

# Monthly documentation review
1. Review documentation structure for organization
2. Check for outdated information
3. Update screenshots and UI references
4. Validate external links still work
```

### **Documentation Validation**
```bash
# Validate documentation consistency
grep -r "Last Updated" docs/                        # Check date consistency
find docs/ -name "*.md" -exec wc -l {} +           # Monitor doc growth
grep -r "TODO\|FIXME" docs/                        # Find incomplete sections

# Test documentation code examples
# Extract and test bash commands from documentation
# Verify all file paths referenced actually exist
```

## 📊 Quality Documentation

### **Quality Documentation Structure**
- **quality/README.md**: Master guide to all quality reports
- **quality/RTM_GUIDE.md**: RTM dashboard and usage
- **quality/TESTING_GUIDE.md**: Comprehensive testing workflows
- **quality/QUICK_REFERENCE.md**: Common commands and thresholds

### **Quality Documentation Commands**
```bash
# Generate quality documentation examples
python tools/report_generator.py --demo             # Generate demo reports for docs
python tools/failure_tracking_demo.py              # Generate failure analysis examples
python tools/archive_cleanup.py --metrics          # Document storage metrics

# Database inspection documentation
python tools/db_inspector.py                       # Document database overview
python tools/db_inspector.py --help                # Document CLI options
```

## 🎯 Specialized Documentation Tasks

### **API Documentation**
```bash
# FastAPI automatic documentation
# Start server and access: http://localhost:8000/docs (Swagger UI)
# Access: http://localhost:8000/redoc (ReDoc)

# Document API endpoints in docs/technical/api-docs/
# Include authentication, request/response examples
# Document error codes and handling
```

### **Architecture Documentation**
```bash
# Document system architecture
# Location: docs/technical/cross-cutting-architecture/
# Include system diagrams, component relationships
# Document technology choices and rationale

# ADR (Architecture Decision Record) documentation
# Location: docs/context/decisions/
# Follow ADR template format
# Document context, decision, consequences
```

### **GDPR Compliance Documentation**
```bash
# GDPR documentation maintenance
# Location: docs/context/compliance/gdpr-requirements.md
# Keep updated with latest requirements
# Document data flows and processing
# Maintain consent mechanism documentation
```

## 🔧 Documentation Tools

### **Documentation Generation**
```bash
# Auto-generate parts of documentation
python tools/rtm_report_generator.py --html         # Generate RTM documentation
python tools/report_generator.py                   # Generate test documentation

# Extract documentation from code
# Use docstrings and comments for API docs
# Generate CLI help documentation from tools
```

### **Documentation Validation Tools**
```bash
# Link checking (manual process)
# 1. Check all [](file.md) references
# 2. Verify all referenced files exist
# 3. Test all command examples
# 4. Validate external URLs

# Documentation linting
# Check markdown formatting consistency
# Verify code block language tags
# Ensure consistent heading hierarchy
```

## 📱 Documentation Accessibility

### **Accessibility Guidelines**
- **Clear Structure**: Use logical heading hierarchy
- **Descriptive Links**: Link text describes destination
- **Alt Text**: Provide descriptions for images/diagrams
- **Plain Language**: Use clear, simple language
- **Consistent Navigation**: Maintain consistent cross-references

### **Mobile-Friendly Documentation**
- **Short Lines**: Keep code examples readable on mobile
- **Clear Sections**: Use clear section breaks
- **Responsive Tables**: Ensure tables work on small screens
- **Touch-Friendly**: Make links easy to tap

## 🔗 Cross-Agent References

- **🔧 Daily Development**: See `.claude/daily-dev.md` for development docs
- **🧪 Testing & Review**: See `.claude/test-review.md` for testing docs
- **🎨 UX/UI Design**: See `.claude/ux-ui-design.md` for design documentation
- **🚨 Emergency**: See `.claude/emergency.md` for troubleshooting docs
- **📖 Main Guide**: See `CLAUDE.md` for project overview

## 💡 Documentation Best Practices

### **Writing Principles**
- **User-Focused**: Write for the reader, not the writer
- **Task-Oriented**: Organize by what users want to accomplish
- **Example-Rich**: Provide plenty of working examples
- **Scannable**: Use headers, lists, and formatting for quick scanning
- **Actionable**: Every document should lead to clear actions

### **Maintenance Principles**
- **Keep Current**: Regular updates prevent documentation debt
- **Test Examples**: All code examples should work
- **Version Control**: Track documentation changes with git
- **Review Process**: Documentation changes need review like code
- **Metrics**: Track documentation usage and effectiveness

---

**🎯 Focus**: This file provides comprehensive documentation workflows and standards. Use for creating, updating, and maintaining all project documentation.**