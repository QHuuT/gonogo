# 📚 Documentation Agent

**Complete documentation workflows and maintenance**

## 🎯 Agent Purpose
This agent specializes in **creating/updating documentation and maintaining cross-references** - documentation workflows, RTM documentation, style guides, and link management.

**🔄 For other tasks**: [Agent Navigation](../CLAUDE.md#🤖-agent-navigation)

## ⚡ Quick Start

### **Documentation Environment Setup**
```bash
# Install documentation dependencies
pip install -e ".[dev]" && pip install jinja2

# Verify RTM and documentation tools
python tools/rtm-db.py admin health-check
python tools/rtm-links.py config-info
```

## 📖 Documentation Workflows

### **Creating New Documentation**
```bash
# 1. Identify documentation need and location
# Technical docs: docs/technical/
# Context/decisions: docs/context/
# User guides: quality/ (for RTM, testing)

# 2. Create documentation following templates
cp docs/technical/template.md docs/technical/new-feature-guide.md

# 3. Update documentation index
# Update docs/README.md with new document link
# Update relevant CLAUDE.md agent sections
```

### **Documentation Standards**
```markdown
# Standard Documentation Structure

## Title (H1 - matches filename)

### Overview (H2)
- Purpose and scope
- Target audience
- Prerequisites

### Implementation/Process (H2)
- Step-by-step procedures
- Code examples with explanations
- Configuration details

### Cross-References (H2)
- Related documentation
- GitHub issues
- RTM connections

### Troubleshooting (H2)
- Common issues
- Solutions
- Emergency contacts/procedures
```

## 🔗 RTM Documentation Management

### **RTM Documentation Workflow**
```bash
# 1. Update RTM database with progress
python tools/rtm-db.py entities update-user-story US-XXXXX --status completed

# 2. Generate current RTM reports
python tools/rtm_report_generator.py --html
# View: http://localhost:8000/api/rtm/reports/matrix?format=html

# 3. Validate all RTM links
python tools/rtm-links.py validate --format json
python tools/rtm-links.py doctor  # Health diagnostics

# 4. Update RTM-related documentation
# Update quality/RTM_GUIDE.md if dashboard changes
# Update CLAUDE.md if new RTM commands added
```

### **RTM Cross-Reference Maintenance**
```bash
# Validate RTM link integrity
python tools/rtm-links.py validate
python tools/rtm-links.py validate --format json > quality/reports/rtm_validation.json

# Generate RTM links for documentation
python tools/rtm-links.py generate-link EP-00005 --bold
python tools/rtm-links.py generate-bdd-link tests/bdd/features/auth.feature user_login

# Update documentation with validated links
python tools/rtm-links.py update --backup  # Creates backup before updates
```

## 📋 Documentation Types & Maintenance

### **Technical Documentation**
```bash
# API Documentation
# Location: docs/technical/api-docs/
# Update after API changes, include examples

# Architecture Documentation
# Location: docs/technical/cross-cutting-architecture/
# Update for major architectural decisions

# Development Workflow Documentation
# Location: docs/technical/development-workflow.md
# Update when processes change

# Quality Assurance Documentation
# Location: docs/technical/quality-assurance.md
# Update for new quality gates or standards
```

### **User Guides & Quality Documentation**
```bash
# RTM User Guide
# Location: quality/RTM_GUIDE.md
# Update when RTM dashboard features change

# Testing Guide
# Location: quality/TESTING_GUIDE.md
# Update when test workflows or tools change

# Quick Reference Guides
# Location: quality/QUICK_REFERENCE.md
# Update for common command changes
```

### **Context & Decision Documentation**
```bash
# Architecture Decision Records (ADRs)
# Location: docs/context/decisions/
# Create new ADR for major technical decisions

# GDPR & Compliance Documentation
# Location: docs/context/compliance/
# Update when privacy requirements change

# Stable Decisions
# Location: docs/context/
# Document unchanging project decisions
```

## 🔧 Agent Documentation Maintenance

### **CLAUDE.md and Agent System**
```bash
# Update main navigation (CLAUDE.md)
# When: New agents added, workflows change, project structure changes

# Update individual agent files
# .claude/daily-dev.md - Daily development commands
# .claude/test-review.md - Testing workflows
# .claude/documentation.md - This file
# .claude/ux-ui-design.md - Design processes
# .claude/emergency.md - Troubleshooting procedures

# Agent cross-reference validation
grep -r "\.claude/" docs/ CLAUDE.md  # Check all agent references
```

### **Command Documentation Updates**
```bash
# When new tools/scripts are added:
# 1. Update relevant agent documentation
# 2. Add to CLAUDE.md quick reference
# 3. Update tool help text and examples
# 4. Add to quality/QUICK_REFERENCE.md if widely used

# Example: New RTM command
echo "# New command: rtm-db.py new-feature" >> .claude/daily-dev.md
echo "python tools/rtm-db.py new-feature --help" >> .claude/daily-dev.md
```

## 📊 Documentation Quality Assurance

### **Documentation Review Checklist**
```bash
# 1. Link Validation
python tools/rtm-links.py validate  # RTM links
# Manual check: All markdown links work
# Tool: Use markdown link checker if available

# 2. Cross-Reference Check
grep -r "docs/" CLAUDE.md .claude/  # Ensure all doc links are valid
grep -r "quality/" CLAUDE.md .claude/  # Check guide references

# 3. Code Example Validation
# Run all code examples in documentation
# Verify commands work in current environment

# 4. Documentation Consistency
# Check formatting consistency across files
# Verify all agent files follow same structure
# Ensure CLAUDE.md navigation is complete
```

### **Documentation Testing**
```bash
# Test all documented commands
bash -n script.sh  # Syntax check bash scripts
python -m py_compile script.py  # Python syntax check

# Test RTM workflows documented
python tools/rtm-db.py admin health-check
python tools/rtm_report_generator.py --html --dry-run

# Validate documentation builds (if using generators)
# Test markdown rendering
# Check for broken internal links
```

## 🔄 Documentation Release Process

### **Before Release Documentation Review**
```bash
# 1. Update version-specific documentation
# Update setup instructions for new requirements
# Update API docs for interface changes
# Update troubleshooting for new known issues

# 2. Generate fresh examples
python tools/rtm_report_generator.py --html  # Updated RTM examples
python tools/report_generator.py --demo     # Updated test report examples

# 3. Validate all external links
# Check GitHub issue links are accessible
# Verify external tool documentation links
# Test deployment guide links

# 4. Update change logs and release notes
# Add to docs/CHANGELOG.md
# Update README.md if needed
# Update CLAUDE.md recent updates section
```

### **Post-Release Documentation Tasks**
```bash
# 1. Archive old documentation
mv docs/legacy/old-version/ docs/legacy/v1.1/

# 2. Update documentation index
# Update docs/README.md with new structure
# Update navigation in CLAUDE.md

# 3. Create documentation for new features
# Follow standard documentation structure
# Add RTM traceability links
# Update relevant agent documentation
```

## 🎨 Documentation Style Guidelines

### **Markdown Standards**
```markdown
# Use consistent heading hierarchy
# H1 for main title (matches filename)
# H2 for major sections
# H3 for subsections
# H4 for details (sparingly)

# Code blocks with language specification
```bash
# Bash commands with descriptions
python tools/example.py --help
```

```python
# Python examples with context
def example_function():
    """Clear docstring."""
    return "documented"
```

# Links with descriptive text
[RTM User Guide](quality/RTM_GUIDE.md) - Complete RTM dashboard usage

# Lists with consistent formatting
- **Bold** for emphasis on key terms
- `code` for commands, filenames, variables
- Use active voice and imperative mood for instructions
```

### **Agent Documentation Standards**
```markdown
# Agent file structure (all agent files follow this):
# 1. Header with emoji and purpose
# 2. Agent Purpose section
# 3. Quick Start section
# 4. Main workflow sections (3-5 sections)
# 5. Cross-references to other agents
# 6. Footer with navigation reminder

# Consistent emoji usage:
# 🎯 for purpose/objectives
# ⚡ for quick start/essential commands
# 🚀 for workflows/processes
# 📊 for analysis/reporting
# 🔧 for tools/configuration
# 🔗 for links/references
# 🚨 for warnings/emergency
```

## 🔍 Documentation Maintenance Scripts

### **Custom Documentation Tools**
```bash
# Link checker (custom script)
# Create: tools/check_doc_links.py
# Purpose: Validate all internal markdown links

# Documentation generator (if needed)
# Create: tools/generate_doc_index.py
# Purpose: Auto-generate docs/README.md index

# Agent cross-reference checker
# Create: tools/validate_agent_refs.py
# Purpose: Ensure all agent cross-references are valid
```

### **Documentation Automation**
```bash
# GitHub workflow integration
# .github/workflows/docs-validation.yml
# Auto-validate documentation on PR

# RTM documentation sync
# Auto-update RTM guides when database changes
python tools/rtm-db.py admin validate
python tools/rtm_report_generator.py --html
```

## 🔗 Integration with Other Agents

- **🔧 Daily Development**: [Daily Dev Agent](.claude/daily-dev.md) - Document daily workflow changes
- **🧪 Test Review**: [Test Review Agent](.claude/test-review.md) - Document testing procedures
- **🎨 UX/UI**: [UX/UI Agent](.claude/ux-ui-design.md) - Document design decisions and standards
- **🚨 Emergency**: [Emergency Agent](.claude/emergency.md) - Document troubleshooting procedures

---

**📖 Remember**: This agent handles all documentation creation and maintenance. For implementing documented features, switch to the appropriate development agent. For urgent documentation fixes, use the Emergency agent.