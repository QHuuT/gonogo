# Code Standards Implementation Guide

**Last Updated**: 2025-09-27
**Related ADR**: [ADR-004: Context-Aware Code Standards](../context/decisions/adr-004-context-aware-code-standards.md)

## 📋 Overview

This guide provides practical implementation details for our context-aware code standards. Unlike traditional one-size-fits-all approaches, we use **different standards for different code contexts** to balance maintainability with developer productivity.

## 🎯 Context-Specific Standards

### Production Code (`src/be/`, `src/fe/`)

**Line Length**: 120 characters
**Enforcement**: Strict
**Tools**: Ruff formatter, pre-commit hooks, CI checks

```bash
# Format production code
ruff format src/ --line-length 120

# Check compliance
python -m flake8 --select=E501 src/
```

**Why 120 characters?**
- Modern standard that accommodates realistic Python patterns
- Fits well on modern wide monitors
- Allows meaningful variable names without artificial abbreviations
- Balances readability with practical constraints

### Test Code (`tests/`)

**Line Length**: No limit (E501 disabled)
**Enforcement**: None
**Rationale**: Test clarity and debugging ability take priority

```python
# ✅ Acceptable in test files
def test_complex_user_story_with_detailed_acceptance_criteria_validation():
    expected_long_description = "Given a user story with very detailed acceptance criteria involving multiple stakeholders and complex business rules..."

    mock_response = {
        "user_story_id": "US-12345",
        "title": "Very long descriptive title that explains exactly what this user story accomplishes...",
        "acceptance_criteria": ["Detailed criterion one", "Detailed criterion two"]
    }
```

### Migration Code (`migrations/`)

**Line Length**: No limit (E501 disabled)
**Enforcement**: None
**Rationale**: Database schema definitions require descriptive names

```python
# ✅ Acceptable in migration files
op.add_column('epics', sa.Column('stakeholder_satisfaction_score_calculated_from_feedback_surveys', sa.Float, nullable=True))
op.add_column('user_stories', sa.Column('gdpr_personal_data_processing_impact_assessment_required', sa.Boolean, server_default='false'))
```

### Utility Code (`tools/`)

**Line Length**: No limit (E501 disabled)
**Enforcement**: None
**Rationale**: Temporary scripts don't warrant formatting overhead

```python
# ✅ Acceptable in tools/
print(f"Processing {total_issues} GitHub issues with labels {epic_label_mapping} for comprehensive sync...")
```

### Template Code

**Approach**: Extract to external Jinja2 templates instead of fighting Python line limits

```python
# ❌ Before: Long HTML strings in Python
def generate_epic_link(epic_id, title, github_issue):
    return f'<a href="{github_url}" target="_blank" class="epic-title-link" title="Click to open {epic_id} in GitHub">{epic_id}: {title}</a>'

# ✅ After: External template
template = env.get_template('epic_link.html')
return template.render(epic_id=epic_id, title=title, github_url=github_url)
```

## 🛠️ Tool Configuration

### flake8 Configuration

Add to `pyproject.toml`:

```toml
[tool.flake8]
max-line-length = 120
per-file-ignores = [
    "tests/*: E501",        # Test clarity over line length
    "migrations/*: E501",   # Database schemas need space
    "tools/*: E501",        # Utility scripts are temporary
    "**/templates.py: E501" # HTML strings should be externalized
]
extend-ignore = [
    "E203",  # Whitespace before ':'
    "W503",  # Line break before binary operator
]
```

### Enable pyproject.toml Support

```bash
# Install flake8-pyproject for pyproject.toml support
pip install flake8-pyproject
```

### Ruff Configuration (Recommended)

```toml
[tool.ruff]
line-length = 120
target-version = "py39"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = ["E501"]  # Let per-file-ignores handle this

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["E501"]
"migrations/*" = ["E501"]
"tools/*" = ["E501"]
"**/templates.py" = ["E501"]
```

## 🚀 Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: Ruff format (production code only)
        entry: ruff format src/
        language: system
        pass_filenames: false

      - id: flake8-production
        name: flake8 production code only
        entry: flake8 src/ --select=E501
        language: system
        pass_filenames: false
```

## 📐 Template Extraction Patterns

### HTML Template Separation

**Before** (rtm_report_generator.py):
```python
html = f"""
<div class="epic-container" data-epic-id="{epic.epic_id}">
    <h3 class="epic-title">{epic_title_link}</h3>
    <div class="epic-metrics">
        <span class="completion-rate">{progress}%</span>
    </div>
</div>
"""
```

**After**:
```python
# templates/epic_container.html
<div class="epic-container" data-epic-id="{{ epic.epic_id }}">
    <h3 class="epic-title">{{ epic_title_link }}</h3>
    <div class="epic-metrics">
        <span class="completion-rate">{{ progress }}%</span>
    </div>
</div>

# Python code
template = env.get_template('epic_container.html')
html = template.render(epic=epic, epic_title_link=epic_title_link, progress=progress)
```

### CSS Separation

**Before**:
```python
css = "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; }"
```

**After**:
```python
# static/css/report.css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    margin: 0;
    padding: 20px;
}

# Python code
<link rel="stylesheet" href="/static/css/report.css">
```

## 🎯 Implementation Workflow

### For New Features
1. **Write production code** following 120-character limit
2. **Write tests** without line length constraints for clarity
3. **Extract templates** for any HTML/CSS content
4. **Run pre-commit hooks** to validate production code standards

### For Existing Code
1. **Apply Ruff formatter** to production code: `ruff format src/ --line-length 120`
2. **Check remaining violations**: `flake8 src/ --select=E501`
3. **Extract templates** for HTML-heavy modules
4. **Accept context-appropriate violations** in tests/tools/migrations

### For Code Reviews
- **Production code**: Enforce 120-character limit
- **Test code**: Focus on clarity over line length
- **Templates**: Encourage externalization over artificial breaks
- **Migrations**: Accept descriptive database names

## ❌ Common Anti-Patterns to Avoid

### Don't Artificially Break Readable Code
```python
# ❌ Bad: Artificial breaks hurt readability
user_story = create_user_story_with_acceptance_criteria(
    title="Short title", epic_id="EP-001", priority="high")

# ✅ Good: Natural breaks or accept longer line
user_story = create_user_story_with_acceptance_criteria(
    title="Short title",
    epic_id="EP-001",
    priority="high"
)

# ✅ Also good: Accept 120+ chars if it's clearer
user_story = create_user_story_with_acceptance_criteria(title="Short title", epic_id="EP-001", priority="high")
```

### Don't Fight Template Strings
```python
# ❌ Bad: Artificial HTML breaks
html = f'<a href="{url}" \\\n    class="link" \\\n    title="{title}">{text}</a>'

# ✅ Good: External template
template = env.get_template('link.html')
html = template.render(url=url, title=title, text=text)
```

## 📊 Success Metrics

### Quantitative
- **Production code E501 violations**: < 10
- **Template extraction rate**: > 80% for HTML-heavy modules
- **Developer time on formatting**: < 5% of development time

### Qualitative
- **Code readability**: Improved in production modules
- **Test clarity**: Maintained with relaxed constraints
- **Developer satisfaction**: Higher with practical standards

## 🔍 Troubleshooting

### flake8 Not Reading pyproject.toml
```bash
# Install the plugin
pip install flake8-pyproject

# Verify configuration
flake8 --version
# Should show: flake8-pyproject installed
```

### Ruff Not Formatting Correctly
```bash
# Check configuration
ruff check --show-settings

# Format specific directory
ruff format src/ --line-length 120 --diff
```

### Pre-commit Hooks Not Working
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

## 📚 References

- [ADR-004: Context-Aware Code Standards](../context/decisions/adr-004-context-aware-code-standards.md)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [flake8-pyproject Plugin](https://pypi.org/project/flake8-pyproject/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/en/stable/templates/)

---

**Remember**: The goal is **meaningful code quality**, not arbitrary compliance with formatting rules. These standards should make development faster and more enjoyable, not slower and more frustrating.