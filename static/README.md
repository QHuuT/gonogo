# Static Assets

This directory contains frontend static assets for the GoNoGo project, following the structure documented in docs/technical/development-workflow.md.

## Directory Structure

```
static/
├── css/               # Global stylesheets
├── js/                # Global JavaScript files
├── images/            # Static images and icons
├── components/        # Component-specific assets
│   ├── rtm/          # RTM-specific components and styles
│   └── common/       # Shared/reusable components
└── README.md         # This file
```

## Integration with FastAPI

Static files are served by FastAPI from this directory:
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

## RTM Frontend Assets

### Current State
- RTM reports use embedded CSS/JS in Python templates
- Report-specific assets are in `quality/reports/assets/`

### US-00002 Improvements
The RTM UX/UI enhancement will:
- Extract inline styles to `static/css/rtm-components.css`
- Move JavaScript to `static/js/rtm-interactions.js`
- Create reusable components in `static/components/rtm/`
- Implement design system in `static/css/design-system.css`

## Relationship to Quality Reports

- **`static/`** - Production static assets served by FastAPI
- **`quality/reports/assets/`** - Generated report assets and templates

For RTM reports, assets will be:
1. Developed in `static/`
2. Referenced by templates in `src/be/templates/`
3. Served via FastAPI static file handling

## Related Documentation
- See docs/technical/development-workflow.md project structure section
- US-00002: Enhanced RTM Report UX/UI Design
- EP-00005: Requirements Traceability Matrix Automation
