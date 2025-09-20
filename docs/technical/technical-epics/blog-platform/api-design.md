# Blog Platform API Design

**Last Updated**: 2025-09-20

## 🎯 API Overview

The blog platform provides both web interface endpoints and optional API endpoints for content consumption. The design focuses on simplicity, performance, and SEO optimization.

## 🌐 Web Interface Endpoints

### Primary Routes

#### `GET /`
**Purpose**: Blog homepage with recent posts
**Response**: HTML page with post listings

```python
@app.get("/", response_class=HTMLResponse)
async def blog_index(request: Request, page: int = 1):
    """
    Display blog homepage with paginated post listings
    """
    posts = await content_service.get_recent_posts(
        page=page,
        per_page=10
    )

    return templates.TemplateResponse("blog/index.html", {
        "request": request,
        "posts": posts,
        "page": page,
        "has_next": len(posts) == 10
    })
```

#### `GET /post/{slug}`
**Purpose**: Individual blog post display
**Response**: HTML page with post content

```python
@app.get("/post/{slug}", response_class=HTMLResponse)
async def blog_post(slug: str, request: Request):
    """
    Display individual blog post by slug
    """
    try:
        post = await content_service.get_post_by_slug(slug)
        seo_data = seo_service.generate_meta_tags(post)

        return templates.TemplateResponse("blog/post.html", {
            "request": request,
            "post": post,
            "seo": seo_data
        })
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
```

### Supporting Routes

#### `GET /feed.xml`
**Purpose**: RSS feed for blog content
**Response**: XML RSS feed

```python
@app.get("/feed.xml", response_class=Response)
async def rss_feed():
    """
    Generate RSS feed for blog posts
    """
    posts = await content_service.get_recent_posts(limit=20)
    rss_content = rss_service.generate_feed(posts)

    return Response(
        content=rss_content,
        media_type="application/rss+xml",
        headers={"Cache-Control": "public, max-age=3600"}
    )
```

#### `GET /sitemap.xml`
**Purpose**: XML sitemap for SEO
**Response**: XML sitemap

```python
@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    """
    Generate XML sitemap for all blog content
    """
    posts = await content_service.get_all_published_posts()
    sitemap_content = seo_service.generate_sitemap(posts)

    return Response(
        content=sitemap_content,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=86400"}
    )
```

## 📊 Data Models

### BlogPost Model

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class BlogPost(BaseModel):
    """
    Blog post data model for both API and template rendering
    """
    title: str = Field(..., description="Post title")
    slug: str = Field(..., description="URL-friendly slug")
    content: str = Field(..., description="Full post content (HTML)")
    excerpt: str = Field(..., description="Post excerpt/summary")
    published_date: datetime = Field(..., description="Publication date")
    updated_date: Optional[datetime] = Field(None, description="Last update date")
    author: str = Field(..., description="Post author name")
    tags: List[str] = Field(default_factory=list, description="Post tags")
    meta_description: str = Field(..., description="SEO meta description")
    featured_image: Optional[str] = Field(None, description="Featured image URL")
    word_count: int = Field(..., description="Estimated word count")
    reading_time: int = Field(..., description="Estimated reading time in minutes")
    is_published: bool = Field(True, description="Publication status")

    class Config:
        schema_extra = {
            "example": {
                "title": "Getting Started with FastAPI",
                "slug": "getting-started-with-fastapi",
                "content": "<h1>Getting Started</h1><p>FastAPI is...</p>",
                "excerpt": "Learn how to build web APIs with FastAPI",
                "published_date": "2025-01-01T10:00:00Z",
                "author": "John Doe",
                "tags": ["python", "fastapi", "web"],
                "meta_description": "Complete guide to FastAPI for beginners",
                "word_count": 1200,
                "reading_time": 5,
                "is_published": True
            }
        }
```

### PostSummary Model

```python
class PostSummary(BaseModel):
    """
    Lightweight post model for listings and API responses
    """
    title: str
    slug: str
    excerpt: str
    published_date: datetime
    author: str
    tags: List[str]
    reading_time: int
    featured_image: Optional[str] = None
```

### SEOData Model

```python
class SEOData(BaseModel):
    """
    SEO metadata for templates and API responses
    """
    title: str
    description: str
    canonical_url: str
    og_title: str
    og_description: str
    og_image: Optional[str] = None
    og_type: str = "article"
    twitter_card: str = "summary_large_image"
    structured_data: dict
```

## 🔧 Service Layer Design

### ContentService

```python
class ContentService:
    """
    Service for content loading and processing
    """

    async def get_all_posts(self) -> List[BlogPost]:
        """Load all published blog posts"""

    async def get_recent_posts(self, limit: int = 10, page: int = 1) -> List[PostSummary]:
        """Get recent posts with pagination"""

    async def get_post_by_slug(self, slug: str) -> BlogPost:
        """Load specific post by slug"""

    async def get_posts_by_tag(self, tag: str) -> List[PostSummary]:
        """Get posts filtered by tag"""

    async def search_posts(self, query: str) -> List[PostSummary]:
        """Search posts by content/title"""

    def process_markdown(self, file_path: str) -> BlogPost:
        """Convert Markdown file to BlogPost model"""
```

### SEOService

```python
class SEOService:
    """
    Service for SEO optimization and metadata generation
    """

    def generate_meta_tags(self, post: BlogPost) -> SEOData:
        """Generate complete SEO metadata for post"""

    def generate_structured_data(self, post: BlogPost) -> dict:
        """Generate JSON-LD structured data"""

    def generate_sitemap(self, posts: List[BlogPost]) -> str:
        """Generate XML sitemap"""

    def generate_rss_feed(self, posts: List[BlogPost]) -> str:
        """Generate RSS feed XML"""
```

## 🎨 Template Data Structure

### Template Context

```python
# Base template context
class TemplateContext(BaseModel):
    request: Request
    site_title: str = "GoNoGo Blog"
    site_description: str = "A GDPR-compliant blog platform"
    current_year: int = datetime.now().year

# Index page context
class IndexContext(TemplateContext):
    posts: List[PostSummary]
    page: int
    has_next: bool
    has_prev: bool
    total_pages: int

# Post page context
class PostContext(TemplateContext):
    post: BlogPost
    seo: SEOData
    related_posts: List[PostSummary]
```

## 🚀 Performance Considerations

### Caching Strategy

```python
from functools import lru_cache
import asyncio

class CachedContentService:
    """
    Content service with caching for performance
    """

    @lru_cache(maxsize=100)
    def get_processed_post(self, file_path: str, last_modified: float) -> BlogPost:
        """Cache processed posts with file modification tracking"""
        return self._process_markdown_file(file_path)

    async def get_recent_posts_cached(self, limit: int = 10) -> List[PostSummary]:
        """Cache recent posts list with TTL"""
        cache_key = f"recent_posts_{limit}"
        cached = await self.cache.get(cache_key)

        if not cached:
            posts = await self.get_recent_posts(limit)
            await self.cache.set(cache_key, posts, ttl=300)  # 5 minutes
            return posts

        return cached
```

### Response Optimization

```python
from fastapi.responses import HTMLResponse
from starlette.responses import Response

async def optimized_blog_post(slug: str, request: Request):
    """
    Optimized post endpoint with caching and compression
    """
    # Check if client has cached version
    if_none_match = request.headers.get("if-none-match")

    post = await content_service.get_post_by_slug(slug)
    etag = generate_etag(post)

    if if_none_match == etag:
        return Response(status_code=304)

    # Render template
    html_content = templates.get_template("blog/post.html").render({
        "request": request,
        "post": post,
        "seo": seo_service.generate_meta_tags(post)
    })

    return HTMLResponse(
        content=html_content,
        headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=3600",
            "Vary": "Accept-Encoding"
        }
    )
```

## 🧪 Testing Endpoints

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient

class TestBlogAPI:

    def test_blog_index_returns_posts(self, client: TestClient):
        """Test homepage returns post listings"""
        response = client.get("/")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text

    def test_blog_post_by_slug(self, client: TestClient):
        """Test individual post retrieval"""
        response = client.get("/post/test-post")
        assert response.status_code == 200

    def test_post_not_found(self, client: TestClient):
        """Test 404 handling for missing posts"""
        response = client.get("/post/nonexistent")
        assert response.status_code == 404

    def test_rss_feed_format(self, client: TestClient):
        """Test RSS feed generation"""
        response = client.get("/feed.xml")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/rss+xml; charset=utf-8"
```

## 📈 Monitoring and Analytics

### Performance Metrics

```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class BlogPerformanceMiddleware(BaseHTTPMiddleware):
    """
    Track performance metrics for blog endpoints
    """

    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        # Log performance metrics
        if request.url.path.startswith("/post/"):
            self.track_post_view(request.url.path, process_time)
        elif request.url.path == "/":
            self.track_homepage_view(process_time)

        response.headers["X-Process-Time"] = str(process_time)
        return response
```

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Implementation Details](implementation.md)
- [Performance Optimization](performance.md)