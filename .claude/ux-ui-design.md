# 🎨 UX/UI Design & Accessibility Agent

**Purpose**: Design harmonization, accessibility standards, and user experience optimization

## 🎨 Design System

### **Color Palette & Branding**
```css
/* Primary Color Palette */
:root {
  --primary-blue: #2563eb;      /* Primary brand color */
  --primary-blue-dark: #1d4ed8; /* Hover states */
  --primary-blue-light: #3b82f6; /* Active states */

  --secondary-gray: #6b7280;    /* Secondary text */
  --secondary-gray-dark: #4b5563; /* Borders */
  --secondary-gray-light: #9ca3af; /* Disabled states */

  --success-green: #059669;     /* Success states */
  --warning-orange: #d97706;    /* Warning states */
  --error-red: #dc2626;         /* Error states */

  --background-white: #ffffff;  /* Main background */
  --background-gray: #f9fafb;   /* Secondary background */
  --background-dark: #111827;   /* Dark mode background */
}
```

### **Typography System**
```css
/* Typography Scale */
:root {
  --font-family-primary: 'Inter', system-ui, sans-serif;
  --font-family-mono: 'JetBrains Mono', monospace;

  --font-size-xs: 0.75rem;      /* 12px */
  --font-size-sm: 0.875rem;     /* 14px */
  --font-size-base: 1rem;       /* 16px */
  --font-size-lg: 1.125rem;     /* 18px */
  --font-size-xl: 1.25rem;      /* 20px */
  --font-size-2xl: 1.5rem;      /* 24px */
  --font-size-3xl: 1.875rem;    /* 30px */

  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
}
```

### **Spacing & Layout**
```css
/* Spacing Scale */
:root {
  --spacing-xs: 0.25rem;        /* 4px */
  --spacing-sm: 0.5rem;         /* 8px */
  --spacing-md: 1rem;           /* 16px */
  --spacing-lg: 1.5rem;         /* 24px */
  --spacing-xl: 2rem;           /* 32px */
  --spacing-2xl: 3rem;          /* 48px */
  --spacing-3xl: 4rem;          /* 64px */

  --border-radius-sm: 0.25rem;  /* 4px */
  --border-radius-md: 0.5rem;   /* 8px */
  --border-radius-lg: 0.75rem;  /* 12px */
}
```

## 🎯 RTM Dashboard Design

### **RTM Dashboard Components**
```bash
# RTM dashboard files location
static/css/rtm-components.css                    # RTM-specific styles
static/css/components.css                        # Reusable components
src/be/templates/rtm/                            # RTM Jinja2 templates

# Generate RTM dashboard for design review
python -m uvicorn src.be.main:app --reload      # Start server
# Access: http://localhost:8000/api/rtm/reports/matrix?format=html

# Generate RTM reports for design validation
python tools/rtm_report_generator.py --html     # Live RTM report
python tools/rtm_demo.py --html                 # Demo RTM report
```

### **RTM Design Standards**
- **Progress Bars**: Use consistent color coding for status (planned, in-progress, completed)
- **Interactive Filters**: Maintain visual feedback for all interactive elements
- **Data Tables**: Responsive design with proper overflow handling
- **Epic Cards**: Consistent card design with clear hierarchy
- **Status Indicators**: Clear visual distinction between statuses

### **RTM Accessibility Features**
```html
<!-- Example: Accessible progress bar -->
<div class="progress-bar" role="progressbar"
     aria-valuenow="65" aria-valuemin="0" aria-valuemax="100"
     aria-label="Epic EP-00005 progress: 65% complete">
  <div class="progress-fill" style="width: 65%"></div>
</div>

<!-- Example: Accessible filter buttons -->
<button class="filter-btn" aria-pressed="false"
        aria-describedby="filter-help">
  Unit Tests
</button>
<div id="filter-help" class="sr-only">
  Filter to show only unit tests
</div>
```

## ♿ Accessibility Standards

### **WCAG 2.1 AA Compliance**
```bash
# Accessibility validation checklist
- [ ] Color contrast ratio ≥ 4.5:1 for normal text
- [ ] Color contrast ratio ≥ 3:1 for large text (18pt+)
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible and consistent
- [ ] Screen reader compatible with ARIA labels
- [ ] Alternative text for all images
- [ ] Logical heading hierarchy (h1 → h2 → h3)
```

### **Keyboard Navigation**
```css
/* Focus indicators */
.focus-visible,
button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
  border-radius: var(--border-radius-sm);
}

/* Skip navigation link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--primary-blue);
  color: white;
  padding: 8px;
  text-decoration: none;
  border-radius: var(--border-radius-sm);
}

.skip-link:focus {
  top: 6px;
}
```

### **Screen Reader Support**
```html
<!-- ARIA landmarks -->
<nav role="navigation" aria-label="Main navigation">
<main role="main" aria-label="Main content">
<aside role="complementary" aria-label="Filters">

<!-- ARIA labels for dynamic content -->
<div aria-live="polite" id="status-updates">
  <!-- Dynamic status messages -->
</div>

<!-- Table accessibility -->
<table role="table" aria-label="Requirements traceability matrix">
  <caption>Epic progress and user story status</caption>
  <thead>
    <tr>
      <th scope="col">Epic</th>
      <th scope="col">Progress</th>
      <th scope="col">Status</th>
    </tr>
  </thead>
</table>
```

## 📱 Responsive Design

### **Breakpoints**
```css
/* Mobile-first responsive design */
:root {
  --breakpoint-sm: 640px;       /* Small tablets */
  --breakpoint-md: 768px;       /* Tablets */
  --breakpoint-lg: 1024px;      /* Laptops */
  --breakpoint-xl: 1280px;      /* Desktops */
}

/* RTM Dashboard responsive behavior */
@media (max-width: 768px) {
  .rtm-table {
    display: block;
    overflow-x: auto;
    white-space: nowrap;
  }

  .epic-card {
    margin-bottom: var(--spacing-md);
    padding: var(--spacing-sm);
  }

  .filter-controls {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}
```

### **Touch-Friendly Design**
```css
/* Touch targets minimum 44x44px */
.touch-target {
  min-height: 44px;
  min-width: 44px;
  padding: var(--spacing-sm);
}

/* Interactive elements */
button, a, input, select {
  min-height: 44px;
  padding: var(--spacing-sm) var(--spacing-md);
}

/* Mobile hover states */
@media (hover: none) {
  .hover-effect:hover {
    /* Disable hover effects on touch devices */
  }
}
```

## 🧩 Component Library

### **Reusable UI Components**
```bash
# Component files location
static/css/components.css                        # Shared component styles
src/be/templates/components/                     # Jinja2 component macros

# Component development workflow
1. Design component in Figma/mockup tool
2. Create CSS in components.css
3. Create Jinja2 macro in templates/components/
4. Test component in RTM dashboard
5. Document component usage
```

### **Button Components**
```css
/* Button variants */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-md);
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background-color: var(--primary-blue);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-blue-dark);
}

.btn-secondary {
  background-color: transparent;
  color: var(--primary-blue);
  border: 1px solid var(--primary-blue);
}

.btn-secondary:hover {
  background-color: var(--primary-blue);
  color: white;
}
```

### **Form Components**
```css
/* Form styling */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--secondary-gray-dark);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid var(--secondary-gray);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Error states */
.form-input.error {
  border-color: var(--error-red);
}

.form-error {
  color: var(--error-red);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-xs);
}
```

## 🎭 Template Design

### **Jinja2 Template Standards**
```bash
# Template file locations
src/be/templates/                                # Main templates
src/be/templates/rtm/                           # RTM-specific templates
src/be/templates/components/                    # Reusable components
src/be/templates/base.html                      # Base template

# Template development workflow
1. Start with base.html for consistent structure
2. Create page-specific templates extending base
3. Use component macros for repeated elements
4. Test templates with real data
5. Validate HTML and accessibility
```

### **Base Template Structure**
```html
<!-- src/be/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}GoNoGo Blog{% endblock %}</title>

    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', path='/css/components.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', path='/css/rtm-components.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Skip navigation for accessibility -->
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <nav role="navigation" aria-label="Main navigation">
        {% block navigation %}{% endblock %}
    </nav>

    <main id="main-content" role="main">
        {% block content %}{% endblock %}
    </main>

    <footer role="contentinfo">
        {% block footer %}{% endblock %}
    </footer>

    <!-- JavaScript -->
    <script src="{{ url_for('static', path='/js/components.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

## 🎨 Design Tools & Workflows

### **Asset Management**
```bash
# Static asset organization
static/
├── css/
│   ├── components.css          # Shared component styles
│   ├── rtm-components.css      # RTM-specific styles
│   └── utilities.css           # Utility classes
├── js/
│   ├── components.js           # Shared JavaScript
│   └── rtm-dashboard.js        # RTM-specific functionality
├── images/
│   ├── icons/                  # SVG icons
│   └── logos/                  # Brand assets
└── fonts/                      # Custom fonts (if any)

# Asset optimization
# Minify CSS for production
# Optimize images for web
# Use SVG for icons when possible
```

### **Design Validation**
```bash
# Design system validation
1. Check color contrast with online tools
2. Test keyboard navigation thoroughly
3. Validate with screen readers (NVDA, JAWS)
4. Test responsive design on multiple devices
5. Validate HTML markup
6. Check performance with Lighthouse

# Visual regression testing
# Take screenshots of key pages
# Compare designs across browsers
# Document any browser-specific issues
```

## 🔄 Performance & Optimization

### **CSS Performance**
```css
/* Efficient CSS practices */
/* Use CSS custom properties for maintainability */
/* Minimize specificity conflicts */
/* Use efficient selectors */

/* Critical CSS inlining for above-the-fold content */
/* Lazy load non-critical CSS */
/* Use CSS containment for large lists */
.rtm-table {
  contain: layout style paint;
}
```

### **JavaScript Performance**
```javascript
// Efficient DOM manipulation
// Use event delegation for dynamic content
// Debounce search and filter inputs
// Lazy load large datasets in RTM dashboard

// Example: Debounced search
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const debouncedSearch = debounce(searchFunction, 300);
```

## 🔗 Cross-Agent References

- **🔧 Daily Development**: See `.claude/daily-dev.md` for development setup
- **🧪 Testing & Review**: See `.claude/test-review.md` for testing UI components
- **📚 Documentation**: See `.claude/documentation.md` for design documentation
- **🚨 Emergency**: See `.claude/emergency.md` for UI troubleshooting
- **📖 Main Guide**: See `CLAUDE.md` for project overview

## 💡 Design Best Practices

### **Design Principles**
- **Consistency**: Use design system components consistently
- **Accessibility**: Design for all users, including disabilities
- **Performance**: Optimize for fast loading and smooth interactions
- **Mobile-First**: Design for mobile devices first, then scale up
- **Progressive Enhancement**: Ensure basic functionality without JavaScript

### **Brand Guidelines**
- **Logo Usage**: Maintain proper spacing and size requirements
- **Color Usage**: Use brand colors consistently and accessibly
- **Typography**: Maintain hierarchy and readability
- **Voice & Tone**: Consistent messaging across all interfaces
- **Imagery**: Use consistent style and quality standards

---

**🎯 Focus**: This file provides comprehensive design standards and accessibility guidelines. Use for maintaining consistent, accessible, and performant user interfaces across the project.**