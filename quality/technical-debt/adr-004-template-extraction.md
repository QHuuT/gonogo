# Technical Debt: Template Extraction for ADR-004 Compliance

**Date**: 2025-09-27
**Priority**: Medium
**Related**: ADR-004 Context-Aware Code Standards

## Problem

After implementing ADR-004 context-aware code standards, we identified 20 remaining E501 line length violations in production code (`src/`). These violations are primarily long HTML template strings embedded in Python code, specifically in:

- `src/be/services/rtm_report_generator.py` (17 violations)
- `src/be/services/svg_graph_generator.py` (2 violations)
- `src/shared/utils/rtm_hybrid_generator.py` (1 violation)

## Technical Debt Details

### Root Cause
The RTM report generator contains extensive HTML template strings that were embedded directly in Python code for rapid prototyping. These strings now violate our 120-character production code standard.

### Current Status (2025-09-27)
- ✅ **Template Infrastructure**: Added Jinja2 environment and helper methods
- ✅ **Template Components**: Created 6 reusable template files
- ✅ **Some Fixes Applied**: Reduced violations from 19 to 13
- 🔄 **Remaining**: 13 violations in complex HTML blocks requiring full template extraction

### Examples of Violations
```python
# Current approach - violates 120-char limit
html += f'<button class="copy-btn" onclick="copyToClipboard(\'{file_path.replace(chr(92), chr(92) + chr(92))}\', this)" title="Copy full path" aria-label="Copy full file path">'

# Also problematic - long CSS/HTML blocks
html += f"""
    <meta name="description" content="Requirements Traceability Matrix for GoNoGo project - Interactive dashboard showing epic progress, user stories, tests, and defects">
"""
```

### Template Infrastructure Added
```python
# Now available in RTMReportGenerator
def _render_template(self, template_name: str, **kwargs) -> str:
    """Render a Jinja2 template with given context."""
    template = self.jinja_env.get_template(template_name)
    return template.render(**kwargs)
```

## ADR-004 Recommended Solution

Per ADR-004 Section 4.3 "Template Code", these HTML strings should be:

1. **Extracted to external Jinja2 templates** in `src/be/templates/rtm/`
2. **Use template inheritance** for common layouts
3. **Separate CSS to external files** in `static/css/`

### Proposed Architecture
```
src/be/templates/rtm/
├── base_report.html          # Base template with common layout
├── epic_card.html           # Epic card component
├── user_stories_table.html  # User stories table component
├── tests_table.html         # Tests table component
└── defects_table.html       # Defects table component

static/css/
├── rtm-components.css       # RTM-specific styles
└── design-system.css        # Existing design system
```

### Implementation Steps
1. Extract HTML blocks to component templates
2. Update `RTMReportGenerator` to use Jinja2 template rendering
3. Move inline CSS to external stylesheets
4. Test template rendering with existing data
5. Update unit tests for new template-based approach

## Temporary Compliance Solution

For immediate ADR-004 compliance, applied manual line breaks to most egregious violations while preserving functionality.

## Effort Estimation

- **Initial Setup** (✅ Completed): 4 hours
- **Remaining Template Extraction**: 6-10 hours
- **CSS Separation**: 2-4 hours
- **Testing & Validation**: 4-6 hours
- **Total Remaining**: 12-20 hours (was 14-22 hours)

## Benefits of Resolution

1. **ADR-004 Compliance**: Eliminates all E501 violations in production code
2. **Template Reusability**: RTM components usable across different views
3. **Designer Collaboration**: HTML/CSS separated from Python logic
4. **Maintainability**: Template changes don't require Python code changes
5. **Performance**: Template caching improves response times

## Timeline

- **Priority**: Medium (not blocking current functionality)
- **Target**: Next major RTM feature development cycle
- **Dependencies**: None (can be done incrementally)

## References

- [ADR-004: Context-Aware Code Standards](../../docs/context/decisions/adr-004-context-aware-code-standards.md)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/en/stable/templates/)
- Current violations list: 20 files, primarily in `rtm_report_generator.py`

---

**Note**: This technical debt item represents architectural improvement opportunity identified during ADR-004 implementation. Resolution will improve code quality and enable better separation of concerns between data generation and presentation layers.