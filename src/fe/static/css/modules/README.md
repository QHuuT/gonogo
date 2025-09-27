# CSS Modules Organization

This directory contains CSS organized into logical modules for better maintainability and scalability.

## Module Structure:

### Core Modules
- `design-system.css` - Design tokens, variables, and foundational styles
- `components.css` - Base component library styles

### Feature Modules
- `rtm-components.css` - RTM (Requirements Traceability Matrix) specific styles
- `failure-reports.css` - Test failure reporting specific styles

### Future Modules (planned)
- `dashboard.css` - Dashboard and analytics styles
- `forms.css` - Form components and validation styles
- `tables.css` - Data table and grid styles
- `utilities.css` - Utility classes and helpers

## Usage

CSS modules should be imported in order of specificity:
1. Design system foundation
2. Base components
3. Feature-specific modules
4. Utilities and overrides