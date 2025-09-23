# 🎨 UX/UI Design & Accessibility Agent

**Design system, accessibility standards, and UI harmonization**

## 🎯 Agent Purpose
This agent specializes in **design tasks, accessibility improvements, and UI consistency** - design system maintenance, accessibility standards, RTM dashboard design, and component library management.

**🔄 For other tasks**: [Agent Navigation](../CLAUDE.md#🤖-agent-navigation)

## ⚡ Quick Start

### **Design Environment Setup**
```bash
# Install development dependencies
pip install -e ".[dev]" && pip install jinja2

# Start server for UI testing
python -m uvicorn src.be.main:app --reload --host 0.0.0.0 --port 8000

# Access RTM dashboard for design review
# http://localhost:8000/api/rtm/reports/matrix?format=html
```

## 🎨 Design System Standards

### **GoNoGo Design Principles**
```css
/* Core Design System */

/* Color Palette */
:root {
  /* Primary Colors */
  --primary-blue: #007bff;
  --primary-dark: #0056b3;
  --primary-light: #66a3ff;

  /* Epic Colors (from GitHub labels) */
  --epic-color: #c5def5;
  --component-color: #f9d0c4;

  /* Status Colors */
  --status-completed: #0e8a16;
  --status-in-progress: #ffd700;
  --status-blocked: #d73a49;
  --status-planned: #6f42c1;

  /* GDPR/Privacy Colors */
  --gdpr-warning: #ff6b6b;
  --privacy-accent: #28a745;

  /* Neutral Colors */
  --background: #ffffff;
  --background-secondary: #f8f9fa;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border: #dee2e6;
}

/* Typography Scale */
--font-size-xs: 0.75rem;    /* 12px */
--font-size-sm: 0.875rem;   /* 14px */
--font-size-base: 1rem;     /* 16px */
--font-size-lg: 1.125rem;   /* 18px */
--font-size-xl: 1.25rem;    /* 20px */
--font-size-2xl: 1.5rem;    /* 24px */
--font-size-3xl: 1.875rem;  /* 30px */

/* Spacing Scale */
--spacing-xs: 0.25rem;      /* 4px */
--spacing-sm: 0.5rem;       /* 8px */
--spacing-md: 1rem;         /* 16px */
--spacing-lg: 1.5rem;       /* 24px */
--spacing-xl: 2rem;         /* 32px */
--spacing-2xl: 3rem;        /* 48px */
```

### **Component Design Standards**
```html
<!-- Standard Button Component -->
<button class="btn btn-primary" aria-label="descriptive action">
  <span>Action Text</span>
</button>

<!-- Data Table Component -->
<table class="table table-responsive" role="table" aria-label="data description">
  <thead>
    <tr>
      <th scope="col" aria-sort="none">Column Header</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data Cell</td>
    </tr>
  </tbody>
</table>

<!-- Form Component -->
<form class="form" novalidate aria-label="form purpose">
  <div class="form-group">
    <label for="input-id" class="form-label">
      Label Text
      <span class="required" aria-label="required">*</span>
    </label>
    <input
      type="text"
      id="input-id"
      class="form-control"
      aria-describedby="input-help"
      required
    >
    <div id="input-help" class="form-text">Help text</div>
  </div>
</form>
```

## 🔧 RTM Dashboard Design

### **RTM Dashboard UI Standards**
```html
<!-- RTM Matrix Table Design -->
<div class="rtm-container" role="main" aria-label="Requirements Traceability Matrix">
  <!-- Filter Controls -->
  <div class="rtm-filters" role="toolbar" aria-label="filter options">
    <div class="filter-group">
      <label for="epic-filter">Epic Filter:</label>
      <select id="epic-filter" class="form-select" aria-label="filter by epic">
        <option value="">All Epics</option>
        <option value="EP-00001">EP-00001: Blog Content</option>
      </select>
    </div>

    <div class="filter-group">
      <label for="status-filter">Status Filter:</label>
      <select id="status-filter" class="form-select" aria-label="filter by status">
        <option value="">All Statuses</option>
        <option value="completed">Completed</option>
        <option value="in-progress">In Progress</option>
      </select>
    </div>
  </div>

  <!-- RTM Matrix -->
  <div class="rtm-matrix" role="grid" aria-label="traceability matrix">
    <table class="table table-bordered table-hover">
      <thead class="table-dark">
        <tr role="row">
          <th scope="col" class="epic-col">Epic</th>
          <th scope="col" class="user-story-col">User Stories</th>
          <th scope="col" class="test-col">Tests</th>
          <th scope="col" class="defect-col">Defects</th>
          <th scope="col" class="progress-col">Progress</th>
        </tr>
      </thead>
      <tbody>
        <!-- Dynamic content with proper ARIA labels -->
      </tbody>
    </table>
  </div>
</div>
```

### **RTM Dashboard Responsive Design**
```css
/* Mobile-First Responsive Design */
.rtm-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-md);
}

/* Tablet and up */
@media (min-width: 768px) {
  .rtm-filters {
    display: flex;
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .filter-group {
    min-width: 200px;
  }
}

/* Desktop and up */
@media (min-width: 992px) {
  .rtm-matrix {
    overflow-x: auto;
  }

  .table {
    min-width: 1000px;
  }
}

/* Large screens */
@media (min-width: 1200px) {
  .rtm-container {
    max-width: 1400px;
  }
}
```

## ♿ Accessibility Standards

### **WCAG 2.1 AA Compliance Checklist**
```html
<!-- Semantic HTML Structure -->
<main role="main" aria-label="main content">
  <h1>Page Title</h1>

  <nav role="navigation" aria-label="page navigation">
    <ul>
      <li><a href="#section1" aria-describedby="nav-help">Section 1</a></li>
    </ul>
  </nav>

  <section id="section1" aria-labelledby="section1-title">
    <h2 id="section1-title">Section Title</h2>
    <!-- Content -->
  </section>
</main>

<!-- Screen Reader Support -->
<div class="sr-only" id="nav-help">
  Use arrow keys to navigate menu items
</div>
```

### **Color Contrast Standards**
```css
/* Ensure 4.5:1 contrast ratio for normal text */
/* Ensure 3:1 contrast ratio for large text (18pt+) */

.text-primary { color: #212529; } /* 16.67:1 on white */
.text-secondary { color: #6c757d; } /* 4.54:1 on white */
.text-success { color: #155724; } /* 5.96:1 on white */
.text-warning { color: #856404; } /* 5.35:1 on white */
.text-danger { color: #721c24; } /* 6.44:1 on white */

/* High contrast mode support */
@media (prefers-contrast: high) {
  .table {
    border: 2px solid #000;
  }

  .btn {
    border: 2px solid currentColor;
  }
}
```

### **Keyboard Navigation**
```css
/* Focus indicators */
:focus {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
}

/* Skip links */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: var(--primary-blue);
  color: white;
  padding: 8px;
  text-decoration: none;
  z-index: 1000;
}

.skip-link:focus {
  top: 6px;
}

/* Keyboard navigation for tables */
.table-responsive {
  overflow-x: auto;
}

.table th, .table td {
  position: relative;
}

.table th:focus, .table td:focus {
  outline: 2px solid var(--primary-blue);
}
```

## 🎯 UI Component Library

### **Form Components**
```html
<!-- Standard Form Input -->
<div class="form-group">
  <label for="input-id" class="form-label required">
    Input Label
    <span aria-label="required field">*</span>
  </label>
  <input
    type="text"
    id="input-id"
    class="form-control"
    aria-describedby="input-help input-error"
    required
    aria-invalid="false"
  >
  <div id="input-help" class="form-text">
    Helpful information about this field
  </div>
  <div id="input-error" class="invalid-feedback" role="alert">
    Error message appears here
  </div>
</div>

<!-- Select Dropdown -->
<div class="form-group">
  <label for="select-id" class="form-label">Select Option</label>
  <select id="select-id" class="form-select" aria-describedby="select-help">
    <option value="">Choose an option</option>
    <option value="option1">Option 1</option>
    <option value="option2">Option 2</option>
  </select>
  <div id="select-help" class="form-text">
    Choose the most appropriate option
  </div>
</div>
```

### **Data Display Components**
```html
<!-- Status Badge -->
<span class="badge status-completed" role="img" aria-label="status completed">
  ✅ Completed
</span>

<span class="badge status-in-progress" role="img" aria-label="status in progress">
  🔄 In Progress
</span>

<span class="badge status-blocked" role="img" aria-label="status blocked">
  🚫 Blocked
</span>

<!-- Progress Bar -->
<div class="progress" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100" aria-label="completion progress">
  <div class="progress-bar" style="width: 75%">
    <span class="sr-only">75% complete</span>
  </div>
</div>

<!-- Data Cards -->
<div class="card" role="article" aria-labelledby="card-title">
  <div class="card-header">
    <h3 id="card-title" class="card-title">Card Title</h3>
  </div>
  <div class="card-body">
    <p class="card-text">Card content with proper semantic structure.</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary" aria-describedby="card-title">
      Action Button
    </button>
  </div>
</div>
```

## 📱 Responsive Design Patterns

### **Mobile-First CSS Approach**
```css
/* Base styles (mobile) */
.container {
  padding: var(--spacing-sm);
  width: 100%;
}

.btn {
  min-height: 44px; /* Touch target size */
  min-width: 44px;
  padding: var(--spacing-sm) var(--spacing-md);
}

.table-responsive {
  display: block;
  overflow-x: auto;
  white-space: nowrap;
}

/* Tablet styles */
@media (min-width: 768px) {
  .container {
    padding: var(--spacing-md);
  }

  .btn-group {
    display: flex;
    gap: var(--spacing-sm);
  }
}

/* Desktop styles */
@media (min-width: 992px) {
  .container {
    padding: var(--spacing-lg);
    max-width: 1200px;
    margin: 0 auto;
  }

  .sidebar {
    display: block;
    width: 250px;
  }

  .main-content {
    margin-left: 250px;
  }
}
```

### **Print Styles**
```css
@media print {
  .no-print {
    display: none !important;
  }

  .table {
    border-collapse: collapse;
    border: 1px solid #000;
  }

  .table th,
  .table td {
    border: 1px solid #000;
    padding: 8px;
  }

  .page-break {
    page-break-before: always;
  }

  a[href]:after {
    content: " (" attr(href) ")";
  }
}
```

## 🔧 Design Implementation Workflow

### **UI Development Process**
```bash
# 1. Design Review
# Review existing UI components in browser
# Check accessibility with browser dev tools
# Test responsive design at different breakpoints

# 2. Component Development
# Create new components following design system
# Test accessibility with screen readers
# Validate HTML semantics

# 3. Integration Testing
# Test with RTM dashboard
# Verify cross-browser compatibility
# Test keyboard navigation

# 4. Documentation Update
# Update component library documentation
# Add accessibility notes
# Update design system guidelines
```

### **Accessibility Testing**
```bash
# Browser-based testing
# Chrome DevTools Lighthouse audit
# Firefox Accessibility Inspector
# Safari VoiceOver testing

# Automated testing tools
npm install -g axe-cli
axe http://localhost:8000/api/rtm/reports/matrix?format=html

# Manual testing checklist
# - Tab navigation works correctly
# - Screen reader announces content properly
# - Color contrast meets WCAG standards
# - Touch targets are at least 44x44px
# - Form labels are properly associated
```

## 🎨 Visual Design Guidelines

### **Typography Hierarchy**
```css
/* Heading Hierarchy */
h1 { font-size: var(--font-size-3xl); font-weight: 700; }
h2 { font-size: var(--font-size-2xl); font-weight: 600; }
h3 { font-size: var(--font-size-xl); font-weight: 600; }
h4 { font-size: var(--font-size-lg); font-weight: 500; }
h5 { font-size: var(--font-size-base); font-weight: 500; }
h6 { font-size: var(--font-size-sm); font-weight: 500; }

/* Body Text */
.text-lead { font-size: var(--font-size-lg); font-weight: 300; }
.text-body { font-size: var(--font-size-base); line-height: 1.5; }
.text-small { font-size: var(--font-size-sm); }
.text-caption { font-size: var(--font-size-xs); }
```

### **Layout Grid System**
```css
/* Flexbox Grid */
.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -15px;
}

.col {
  flex: 1;
  padding: 0 15px;
}

.col-auto { flex: 0 0 auto; }
.col-12 { flex: 0 0 100%; }
.col-6 { flex: 0 0 50%; }
.col-4 { flex: 0 0 33.333333%; }
.col-3 { flex: 0 0 25%; }

/* Responsive columns */
@media (min-width: 768px) {
  .col-md-6 { flex: 0 0 50%; }
  .col-md-4 { flex: 0 0 33.333333%; }
}
```

## 📊 RTM Dashboard Specific Design

### **RTM Matrix Styling**
```css
/* RTM-specific component styles */
.rtm-matrix .table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.rtm-matrix .epic-column {
  background-color: var(--epic-color);
  min-width: 150px;
}

.rtm-matrix .status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: var(--font-size-sm);
  font-weight: 500;
}

.rtm-matrix .progress-bar {
  height: 20px;
  border-radius: 10px;
  background: linear-gradient(90deg, var(--status-completed) 0%, var(--status-completed) var(--progress), var(--background-secondary) var(--progress));
}

/* Horizontal scroll enhancement */
.rtm-matrix {
  position: relative;
}

.rtm-matrix::after {
  content: "← Scroll horizontally to see more columns →";
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  text-align: center;
}

@media (min-width: 992px) {
  .rtm-matrix::after {
    display: none;
  }
}
```

## 🔗 Integration with Other Agents

- **🔧 Daily Development**: [Daily Dev Agent](.claude/daily-dev.md) - Implement UI changes
- **🧪 Test Review**: [Test Review Agent](.claude/test-review.md) - UI accessibility testing
- **📚 Documentation**: [Documentation Agent](.claude/documentation.md) - Document design decisions
- **🚨 Emergency**: [Emergency Agent](.claude/emergency.md) - Fix UI breaking issues

---

**📖 Remember**: This agent handles all design and accessibility concerns. For implementing design changes, coordinate with the Daily Dev agent. For documenting design decisions, use the Documentation agent.