# Blog Platform Performance

**Last Updated**: 2025-09-20

## 🎯 Performance Targets

### Core Web Vitals
- **First Contentful Paint (FCP)**: < 1.2 seconds
- **Largest Contentful Paint (LCP)**: < 2.0 seconds
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Time to Interactive (TTI)**: < 2.5 seconds

### Lighthouse Scores (Target: > 90)
- **Performance**: > 90
- **Accessibility**: > 95
- **Best Practices**: > 90
- **SEO**: > 95

### Custom Metrics
- **Page Load Time**: < 2 seconds (average)
- **Time to First Byte (TTFB)**: < 200ms
- **Template Rendering Time**: < 50ms
- **Content Processing Time**: < 100ms

## 🚀 Optimization Strategies

### 1. Server-Side Optimization

#### Content Caching
```python
from functools import lru_cache
from typing import Dict, List
import time

class ContentCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size

    @lru_cache(maxsize=100)
    def get_post(self, slug: str, last_modified: float) -> BlogPost:
        """Cache processed posts with file modification tracking"""
        return self._process_post(slug)

    def invalidate_cache(self):
        """Clear cache when content changes detected"""
        self.get_post.cache_clear()
```

#### Template Compilation Caching
```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Enable template caching in production
env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=400,  # Template compilation cache
    auto_reload=False  # Disable in production
)
```

#### Database Query Optimization
```python
# Use async operations for non-blocking I/O
async def get_recent_posts(limit: int = 10) -> List[BlogPost]:
    """Async content loading for better concurrency"""
    posts = await asyncio.gather(*[
        load_post_async(file) for file in recent_files[:limit]
    ])
    return sorted(posts, key=lambda p: p.published_date, reverse=True)
```

### 2. Response Optimization

#### HTTP Compression
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
    compresslevel=6     # Balance between speed and compression
)
```

#### Response Headers
```python
from fastapi import Response

def set_cache_headers(response: Response, max_age: int = 3600):
    """Set appropriate cache headers for static content"""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    response.headers["ETag"] = generate_etag(content)
    return response
```

#### Content Delivery Optimization
```python
# Static file serving with optimization
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

# CSS/JS minification for production
def minify_assets():
    """Minify CSS and JavaScript files"""
    # Implementation for asset minification
    pass
```

### 3. Frontend Optimization

#### Critical CSS Inlining
```html
<!-- Inline critical CSS for above-the-fold content -->
<style>
    /* Critical CSS for header and initial content */
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    header { background: #333; color: white; padding: 1rem; }
    .hero { font-size: 2rem; margin: 2rem 0; }
</style>

<!-- Load full CSS asynchronously -->
<link rel="preload" href="/static/css/main.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
```

#### Image Optimization
```html
<!-- Responsive images with modern formats -->
<picture>
    <source srcset="/static/images/hero.webp" type="image/webp">
    <source srcset="/static/images/hero.avif" type="image/avif">
    <img src="/static/images/hero.jpg"
         alt="Hero image"
         loading="lazy"
         width="800"
         height="400">
</picture>
```

#### Resource Hints
```html
<head>
    <!-- DNS prefetch for external resources -->
    <link rel="dns-prefetch" href="//fonts.googleapis.com">

    <!-- Preconnect to critical external origins -->
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

    <!-- Preload critical resources -->
    <link rel="preload" href="/static/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
</head>
```

## 📊 Performance Monitoring

### 1. Server-Side Metrics

#### Response Time Tracking
```python
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log slow requests
        if process_time > 1.0:
            logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")

        response.headers["X-Process-Time"] = str(process_time)
        return response
```

#### Resource Usage Monitoring
```python
import psutil
from typing import Dict

def get_performance_metrics() -> Dict[str, float]:
    """Collect server performance metrics"""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "active_connections": len(psutil.net_connections())
    }
```

### 2. Frontend Performance Tracking

#### Core Web Vitals Measurement
```javascript
// Measure and report Core Web Vitals
import {getCLS, getFID, getFCP, getLCP, getTTFB} from 'web-vitals';

function sendToAnalytics(metric) {
    // Send performance data to monitoring service
    fetch('/api/metrics', {
        method: 'POST',
        body: JSON.stringify(metric)
    });
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

#### Performance Observer API
```javascript
// Monitor resource loading performance
const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        if (entry.duration > 1000) {
            console.warn(`Slow resource: ${entry.name} took ${entry.duration}ms`);
        }
    }
});

observer.observe({entryTypes: ['resource', 'navigation']});
```

## 🧪 Performance Testing

### 1. Load Testing
```python
# Using locust for load testing
from locust import HttpUser, task, between

class BlogUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_homepage(self):
        self.client.get("/")

    @task(2)
    def view_random_post(self):
        # Test random blog post viewing
        post_slug = self.get_random_post_slug()
        self.client.get(f"/post/{post_slug}")

    @task(1)
    def view_about_page(self):
        self.client.get("/about")
```

### 2. Benchmark Testing
```python
import asyncio
import time
from typing import List

async def benchmark_content_loading():
    """Benchmark content processing performance"""
    start_time = time.time()

    # Load all posts concurrently
    posts = await load_all_posts()

    end_time = time.time()
    processing_time = end_time - start_time

    print(f"Loaded {len(posts)} posts in {processing_time:.2f} seconds")
    print(f"Average time per post: {processing_time / len(posts):.3f} seconds")
```

### 3. Lighthouse CI Integration
```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [push]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install Lighthouse CI
        run: npm install -g @lhci/cli@0.12.x
      - name: Run Lighthouse CI
        run: lhci autorun
```

## 🎯 Performance Budget

### Page Weight Limits
- **HTML**: < 50KB (compressed)
- **CSS**: < 30KB (compressed)
- **JavaScript**: < 50KB (compressed)
- **Images**: < 500KB per page
- **Total Page Weight**: < 1MB

### Resource Limits
- **HTTP Requests**: < 50 per page
- **Third-party Scripts**: < 3 external domains
- **Web Fonts**: < 2 font families, < 4 variants

### Response Time Budgets
- **Homepage**: < 1.5 seconds
- **Blog Posts**: < 2.0 seconds
- **Search Results**: < 1.0 seconds
- **Static Assets**: < 500ms

## 🔧 Optimization Checklist

### Server-Side
- [ ] Content caching implemented
- [ ] Template compilation caching enabled
- [ ] Gzip compression configured
- [ ] Async operations for I/O
- [ ] Proper HTTP headers set
- [ ] Database queries optimized

### Frontend
- [ ] Critical CSS inlined
- [ ] Images optimized and lazy-loaded
- [ ] Modern image formats (WebP, AVIF)
- [ ] Resource hints implemented
- [ ] JavaScript minified and deferred
- [ ] Web fonts optimized

### Monitoring
- [ ] Performance middleware implemented
- [ ] Core Web Vitals tracking
- [ ] Lighthouse CI configured
- [ ] Load testing setup
- [ ] Performance budgets defined
- [ ] Alerting for performance regressions

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Implementation Details](implementation.md)
- [API Design](api-design.md)