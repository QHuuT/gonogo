# ADR-005: Frontend-Backend Separation Architecture

**Status**: Accepted
**Date**: 2025-09-27
**Deciders**: Development Team
**Related**: [ADR-001: Technology Stack](adr-001-technology-stack-selection.md), [ADR-004: Code Standards](adr-004-context-aware-code-standards.md)

## Context

### The Problem: Embedded HTML in Python Functions

During technical debt cleanup following ADR-004 implementation, we discovered **230+ lines of embedded HTML/CSS code within Python functions** that violated separation of concerns principles:

1. **failure_reporter.py**: Complete HTML reports and CSS styles embedded as Python f-strings
2. **rtm_report_generator.py**: Template fragments mixed with business logic
3. **Template coupling**: Backend services directly manipulating HTML structure
4. **Asset management**: No organized approach to CSS/JS bundling and optimization

### Architecture Smell Indicators

- HTML templates scattered across Python business logic
- Inline CSS styles hardcoded in Python strings
- No clear separation between presentation and data layers
- Difficulty testing frontend components independently
- Asset optimization handled ad-hoc without build system

### Technical Debt Assessment

The embedded HTML approach created several maintenance issues:
- Frontend changes required modifying Python backend code
- No template reusability or component abstraction
- Testing presentation logic required running backend services
- Static asset management was manual and error-prone

## Decision

We will implement a **comprehensive frontend-backend separation architecture** with dedicated directory structures, service boundaries, and build systems.

### Architecture Principles

1. **Clear Separation of Concerns**: Frontend presentation logic separated from backend business logic
2. **Service Boundaries**: Well-defined APIs between frontend and backend layers
3. **Component Architecture**: Reusable template components with organized asset management
4. **Build System**: Automated asset bundling, minification, and cache busting

## Implementation

### Directory Structure

```
src/
├── be/                 # Backend services and business logic
│   ├── api/           # FastAPI endpoints and routes
│   ├── models/        # Database models and business entities
│   └── services/      # Business logic and data processing
├── fe/                 # Frontend templates, components, and assets
│   ├── templates/     # Jinja2 templates organized by feature
│   ├── static/        # CSS, JS, and static assets
│   ├── services/      # Frontend-specific services
│   ├── interfaces/    # Data contracts and API boundaries
│   ├── views/         # View controllers for template rendering
│   └── build/         # Asset bundling and optimization system
└── shared/            # Shared utilities and cross-cutting concerns
```

### Service Layer Architecture

#### Frontend Services

1. **TemplateService**: Core template rendering with Jinja2 engine
2. **ComponentService**: High-level component generation and composition
3. **AssetService**: Static asset management and optimization
4. **ViewControllers**: Feature-specific view logic (RTM, Reports, etc.)

#### Backend Integration

- Backend services use frontend services through well-defined interfaces
- Data contracts ensure type safety between layers
- Clear API boundaries prevent tight coupling

### Build System

#### Asset Bundling Configuration (`src/fe/static/assets.json`)

```json
{
  "bundles": {
    "app": {
      "css": ["components/base.css", "components/cards.css"],
      "js": ["app/main.js", "app/navigation.js"]
    },
    "reports": {
      "css": ["reports/failure-reports.css", "reports/rtm.css"]
    }
  }
}
```

#### Build Commands

- **Development**: `python build.py dev` (no minification, fast builds)
- **Production**: `python build.py prod` (minified, optimized, cache-busted)
- **Watch Mode**: `python build.py watch` (auto-rebuild on changes)

#### Build Outputs

```
static/build/
├── app.bundle.css      # Combined and minified app styles
├── app.bundle.js       # Combined and minified app scripts
├── reports.bundle.css  # Feature-specific style bundles
└── manifest.json       # Cache-busted asset URLs
```

### Template Component Architecture

#### Before: Embedded HTML in Python

```python
def generate_failure_report(self):
    html = f"""
    <div class="failure-card" style="border: 1px solid #e74c3c;">
        <h3>{self.test_name}</h3>
        <div class="error-details">{self.error_message}</div>
    </div>
    """
    return html
```

#### After: Template Components

```python
# Backend service
def generate_failure_report(self):
    data = FailureReportData(
        test_name=self.test_name,
        error_message=self.error_message,
        timestamp=self.timestamp
    )
    return self.template_service.render('reports/failure_report.html', data)
```

```html
<!-- src/fe/templates/reports/failure_report.html -->
<div class="failure-card">
    <h3>{{ test_name }}</h3>
    <div class="error-details">{{ error_message }}</div>
    <div class="timestamp">{{ timestamp }}</div>
</div>
```

## Consequences

### Positive

1. **Clean Separation**: Frontend and backend concerns are clearly separated
2. **Maintainability**: Template changes don't require modifying Python code
3. **Reusability**: Component-based templates can be reused across features
4. **Performance**: Asset bundling reduces HTTP requests and file sizes
5. **Developer Experience**: Clear build commands and organized structure
6. **Testability**: Frontend components can be tested independently

### Negative

1. **Complexity**: More sophisticated build system and directory structure
2. **Learning Curve**: Developers need to understand frontend service architecture
3. **Build Step**: Production deployments require running build process

### Neutral

1. **File Count**: More files but better organization
2. **Build Time**: Minimal overhead (dev: 0.01s, prod: 0.02s)

## Monitoring and Success Criteria

### Immediate Benefits

- ✅ Extracted 230+ lines of embedded HTML from Python functions
- ✅ Created reusable template components (metric cards, epic headers)
- ✅ Implemented asset bundling with cache busting
- ✅ Established clear service boundaries and data contracts

### Long-term Goals

- Reduced frontend development cycle time
- Improved template reusability metrics
- Better separation of frontend/backend team responsibilities
- Enhanced performance through optimized asset delivery

## Related Decisions

- **ADR-001**: Technology stack selection (Jinja2, FastAPI)
- **ADR-004**: Context-aware code standards (production vs. development code)

## Implementation Notes

### Migration Strategy

1. **Phase 1**: Extract embedded HTML to external templates ✅
2. **Phase 2**: Create frontend service layer ✅
3. **Phase 3**: Implement asset bundling system ✅
4. **Phase 4**: Establish clear API boundaries ✅

### Build System Integration

The build system integrates with existing development workflow:
- Development mode for fast iteration
- Production mode for optimized deployment
- Watch mode for continuous development

### Backward Compatibility

All existing functionality maintained while improving architecture:
- RTM report generation continues to work
- Failure reporting maintains same output format
- Template rendering performance improved through caching