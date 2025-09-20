# RTM Automation Evolution Guide

**Document Purpose**: Guide for extending and evolving the Requirements Traceability Matrix automation system
**Created**: 2025-09-20
**Related Epic**: [EP-00005: RTM Automation](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00005)

## 🎯 Architecture Overview

The RTM automation system is designed with extensibility in mind, using a plugin architecture that allows easy addition of new link types, validation rules, and output formats.

```
RTM Automation Architecture:
├── Core Engine (src/shared/utils/rtm_link_generator.py)
│   ├── RTM Parser - Extracts references from markdown
│   ├── Link Generator - Creates clickable links
│   └── Validator - Checks link accuracy
├── Plugin System (src/shared/utils/rtm_plugins/)
│   ├── link_generators/ - Custom link types
│   ├── validators/ - Custom validation rules
│   └── parsers/ - Different RTM formats
├── Configuration (config/rtm-automation.yml)
├── CLI Tool (tools/rtm-links.py)
└── GitHub Action (.github/workflows/rtm-link-update.yml)
```

## 🔧 How to Add New Link Types

### **Step 1: Create Link Generator Plugin**

Create a new plugin in `src/shared/utils/rtm_plugins/link_generators/`:

```python
# custom_link_generator.py
from typing import Dict, Optional
from ..base_link_generator import BaseLinkGenerator

class CustomLinkGenerator(BaseLinkGenerator):
    """Generate links for custom reference types."""

    def can_handle(self, reference_type: str) -> bool:
        """Return True if this generator handles the reference type."""
        return reference_type.startswith("CUSTOM-")

    def generate_link(self, reference: str, context: Dict) -> Optional[str]:
        """Generate clickable link for custom reference."""
        # Extract custom ID from reference
        custom_id = self.extract_id(reference)

        # Generate appropriate link based on your system
        return f"[{reference}](https://your-system.com/custom/{custom_id})"

    def validate_link(self, reference: str, context: Dict) -> bool:
        """Validate that the custom reference exists."""
        # Implement validation logic
        return self.check_custom_system(reference)
```

### **Step 2: Register Plugin in Configuration**

Update `config/rtm-automation.yml`:

```yaml
link_generators:
  - name: "github_issues"
    class: "GitHubIssueLinkGenerator"
    enabled: true
  - name: "bdd_scenarios"
    class: "BDDScenarioLinkGenerator"
    enabled: true
  - name: "custom_references"  # Add your plugin
    class: "CustomLinkGenerator"
    enabled: true
    config:
      api_endpoint: "https://your-system.com/api"
      timeout: 30
```

### **Step 3: Update RTM Link Types Documentation**

Add your new link type to `docs/technical/documentation-workflow.md`:

```markdown
**Custom Reference Links**:
- **Format**: `[CUSTOM-XXXXX](https://your-system.com/custom/XXXXX)`
- **Purpose**: Direct navigation to custom system references
- **Example**: `[CUSTOM-00001](https://your-system.com/custom/00001)`
```

### **Step 4: Add Tests**

Create tests in `tests/unit/test_custom_link_generator.py`:

```python
def test_custom_link_generation():
    generator = CustomLinkGenerator()
    result = generator.generate_link("CUSTOM-00001", {})
    assert result == "[CUSTOM-00001](https://your-system.com/custom/00001)"

def test_custom_link_validation():
    generator = CustomLinkGenerator()
    assert generator.validate_link("CUSTOM-00001", {}) is True
```

## 📝 How to Support New RTM Formats

### **Step 1: Create Parser Plugin**

Create a new parser in `src/shared/utils/rtm_plugins/parsers/`:

```python
# custom_rtm_parser.py
from typing import List, Dict
from ..base_rtm_parser import BaseRTMParser

class CustomRTMParser(BaseRTMParser):
    """Parse custom RTM format."""

    def can_parse(self, content: str) -> bool:
        """Return True if this parser can handle the content format."""
        return "<!-- CUSTOM-RTM-FORMAT -->" in content

    def parse_requirements(self, content: str) -> List[Dict]:
        """Extract requirements from custom format."""
        # Implement parsing logic for your format
        return self.extract_custom_format(content)

    def parse_user_stories(self, content: str) -> List[Dict]:
        """Extract user stories from custom format."""
        # Implement user story extraction
        return self.extract_user_stories_custom(content)
```

### **Step 2: Update Configuration**

```yaml
parsers:
  - name: "standard_markdown"
    class: "StandardMarkdownParser"
    enabled: true
  - name: "custom_format"
    class: "CustomRTMParser"
    enabled: true
    priority: 10  # Higher priority = checked first
```

## 🔍 How to Add Custom Validation Rules

### **Step 1: Create Validator Plugin**

```python
# custom_validator.py
from typing import Dict, List
from ..base_validator import BaseValidator

class CustomValidator(BaseValidator):
    """Custom validation rules for RTM links."""

    def validate_requirement(self, requirement: Dict) -> List[str]:
        """Validate a single requirement row."""
        errors = []

        # Add your custom validation logic
        if not self.check_custom_business_rule(requirement):
            errors.append("Custom business rule violation")

        return errors

    def validate_cross_references(self, rtm_data: Dict) -> List[str]:
        """Validate cross-references between different sections."""
        errors = []

        # Check consistency across RTM sections
        if not self.validate_epic_consistency(rtm_data):
            errors.append("Epic consistency check failed")

        return errors
```

### **Step 2: Register Validator**

```yaml
validators:
  - name: "standard_validation"
    class: "StandardValidator"
    enabled: true
  - name: "custom_business_rules"
    class: "CustomValidator"
    enabled: true
    config:
      strict_mode: true
      business_rules:
        - "epic_user_story_consistency"
        - "requirement_priority_alignment"
```

## 🎨 How to Add New Output Formats

### **Step 1: Create Output Plugin**

```python
# html_output_generator.py
from typing import Dict
from ..base_output_generator import BaseOutputGenerator

class HTMLOutputGenerator(BaseOutputGenerator):
    """Generate HTML output from RTM data."""

    def generate(self, rtm_data: Dict, output_path: str) -> None:
        """Generate HTML RTM output."""
        html_content = self.render_html_template(rtm_data)
        self.write_file(output_path, html_content)

    def get_file_extension(self) -> str:
        return ".html"

    def render_html_template(self, data: Dict) -> str:
        """Render RTM data as HTML."""
        # Use Jinja2 templates or similar
        return self.template_engine.render("rtm.html", data)
```

### **Step 2: Add CLI Support**

Update `tools/rtm-links.py`:

```python
@click.command()
@click.option('--format', type=click.Choice(['markdown', 'html', 'pdf']),
              default='markdown', help='Output format')
def generate(format):
    """Generate RTM with specified output format."""
    generator = get_output_generator(format)
    rtm_data = parse_rtm_file("docs/traceability/requirements-matrix.md")
    generator.generate(rtm_data, f"output/rtm.{generator.get_file_extension()}")
```

## 📊 How to Modify GitHub URL Patterns

### **Update Configuration**

```yaml
github_patterns:
  issue_search: "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{id}"
  epic_search: "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+label%3Aepic+{id}"
  milestone_search: "https://github.com/{owner}/{repo}/milestones?q={id}"

  # Add custom patterns
  custom_search: "https://github.com/{owner}/{repo}/issues?q=is%3Aissue+{custom_query}"
```

### **Update Link Generator**

```python
def generate_github_link(self, reference: str, link_type: str) -> str:
    """Generate GitHub link using configurable patterns."""
    pattern = self.config.get_pattern(link_type)
    return pattern.format(
        owner=self.config.github_owner,
        repo=self.config.github_repo,
        id=reference,
        custom_query=self.build_custom_query(reference)
    )
```

## 🔄 Performance Optimization Strategies

### **For Large RTM Files**

1. **Implement Caching**:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def validate_github_issue(self, issue_id: str) -> bool:
       """Cache GitHub API validation results."""
       return self.github_client.issue_exists(issue_id)
   ```

2. **Parallel Processing**:
   ```python
   import concurrent.futures

   def validate_links_parallel(self, links: List[str]) -> List[bool]:
       """Validate multiple links in parallel."""
       with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
           return list(executor.map(self.validate_link, links))
   ```

3. **Incremental Updates**:
   ```python
   def update_rtm_incremental(self, changed_files: List[str]) -> None:
       """Only update RTM sections affected by file changes."""
       affected_sections = self.identify_affected_sections(changed_files)
       for section in affected_sections:
           self.update_section(section)
   ```

## 🧪 Testing Strategy for Extensions

### **Unit Tests for Plugins**

```python
# tests/unit/test_custom_plugin.py
import pytest
from src.shared.utils.rtm_plugins.custom_plugin import CustomPlugin

class TestCustomPlugin:
    def test_plugin_registration(self):
        plugin = CustomPlugin()
        assert plugin.name == "custom_plugin"
        assert plugin.version == "1.0.0"

    def test_custom_functionality(self):
        plugin = CustomPlugin()
        result = plugin.process("test input")
        assert result == "expected output"
```

### **Integration Tests**

```python
# tests/integration/test_rtm_with_custom_plugin.py
def test_rtm_generation_with_custom_plugin():
    """Test RTM generation including custom plugin."""
    rtm_generator = RTMLinkGenerator()
    rtm_generator.register_plugin(CustomPlugin())

    result = rtm_generator.generate_links(test_rtm_content)
    assert "custom-link-format" in result
```

## 🚀 Migration Guide for Breaking Changes

### **Version 1.x to 2.x Migration**

If you need to make breaking changes to the plugin API:

1. **Deprecation Period**:
   ```python
   # Mark old methods as deprecated
   @deprecated("Use new_method() instead. Will be removed in v3.0")
   def old_method(self):
       return self.new_method()
   ```

2. **Configuration Migration**:
   ```python
   def migrate_config_v1_to_v2(old_config: Dict) -> Dict:
       """Migrate configuration from v1 to v2 format."""
       new_config = {}
       # Migration logic here
       return new_config
   ```

3. **Data Format Migration**:
   ```python
   def migrate_rtm_format(rtm_content: str) -> str:
       """Migrate RTM from old format to new format."""
       # Format migration logic
       return updated_content
   ```

## 📞 Support and Troubleshooting

### **Common Extension Issues**

1. **Plugin Not Loading**:
   - Check plugin is in correct directory
   - Verify configuration syntax
   - Check Python import paths

2. **Link Generation Failing**:
   - Verify API endpoints are accessible
   - Check authentication credentials
   - Review rate limiting settings

3. **Performance Issues**:
   - Enable caching for expensive operations
   - Use parallel processing for bulk operations
   - Implement incremental updates

### **Getting Help**

- **Documentation**: This guide and `docs/technical/documentation-workflow.md`
- **GitHub Issues**: Create issue with `rtm-automation` label
- **Code Examples**: See `tests/` directory for working examples

---

**Related Documentation**:
- [Documentation Workflow](documentation-workflow.md) - RTM link management process
- [Requirements Matrix](../traceability/requirements-matrix.md) - Current RTM
- [EP-00005 RTM Automation](https://github.com/QHuuT/gonogo/issues?q=is%3Aissue+EP-00005) - Implementation tracking