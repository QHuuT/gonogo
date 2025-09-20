# Comment System Performance

**Last Updated**: 2025-09-20

## 🎯 Performance Targets

### Response Time Requirements
- **Comment Submission**: < 1.0 seconds
- **Comment Display**: < 0.5 seconds
- **Moderation Actions**: < 0.3 seconds
- **GDPR Rights Requests**: < 5.0 seconds (access), < 10.0 seconds (erasure)

### Throughput Requirements
- **Comment Submissions**: 100 comments/minute sustained
- **Comment Reads**: 10,000 reads/minute sustained
- **Moderation Queue**: 1,000 items/hour processing capacity
- **Concurrent Users**: 500 simultaneous comment interactions

### System Availability
- **Uptime Target**: 99.9% (8.77 hours downtime/year)
- **Recovery Time**: < 5 minutes for comment system failures
- **Data Consistency**: Eventually consistent within 1 second
- **Backup Recovery**: < 1 hour RTO for complete system restoration

## 🚀 Optimization Strategies

### 1. Database Optimization

#### Indexing Strategy
```sql
-- Optimized indexes for comment queries
CREATE INDEX idx_comments_post_slug_status ON comments(post_slug, status);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);
CREATE INDEX idx_moderation_queue_priority ON moderation_queue(priority, queued_at);
CREATE INDEX idx_personal_data_comment_id ON personal_data(comment_id);
CREATE INDEX idx_consent_records_timestamp ON consent_records(timestamp);

-- Partial indexes for active data
CREATE INDEX idx_active_comments ON comments(post_slug)
WHERE status = 'approved' AND deleted_at IS NULL;
```

#### Query Optimization
```python
class OptimizedCommentRepository:
    async def get_comments_for_post(
        self,
        post_slug: str,
        limit: int = 50
    ) -> List[Comment]:
        """
        Optimized query for comment retrieval with minimal joins
        """
        query = """
        SELECT c.id, c.content, c.created_at, c.status,
               pd.display_name
        FROM comments c
        LEFT JOIN personal_data pd ON c.id = pd.comment_id
            AND pd.consent_name_display = true
        WHERE c.post_slug = $1
            AND c.status = 'approved'
            AND c.deleted_at IS NULL
        ORDER BY c.created_at ASC
        LIMIT $2
        """
        return await self.database.fetch_all(query, post_slug, limit)

    async def get_moderation_queue_batch(
        self,
        batch_size: int = 20
    ) -> List[ModerationItem]:
        """
        Efficient batch processing for moderation queue
        """
        query = """
        SELECT mq.comment_id, mq.priority, mq.flags,
               c.content, c.post_slug, c.created_at
        FROM moderation_queue mq
        JOIN comments c ON mq.comment_id = c.id
        WHERE mq.processed_at IS NULL
        ORDER BY mq.priority DESC, mq.queued_at ASC
        LIMIT $1
        FOR UPDATE SKIP LOCKED
        """
        return await self.database.fetch_all(query, batch_size)
```

### 2. Caching Strategy

#### Multi-Level Caching
```python
from typing import Optional
import asyncio
from functools import lru_cache

class CommentCacheService:
    def __init__(self):
        self.redis_client = Redis()
        self.local_cache = {}

    async def get_post_comments(
        self,
        post_slug: str
    ) -> Optional[List[CommentDisplay]]:
        """
        Multi-level caching: Memory → Redis → Database
        """
        # L1: Memory cache (fastest)
        cache_key = f"comments:{post_slug}"
        if cache_key in self.local_cache:
            return self.local_cache[cache_key]

        # L2: Redis cache (fast)
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            comments = json.loads(cached_data)
            self.local_cache[cache_key] = comments  # Populate L1
            return comments

        # L3: Database (slowest)
        comments = await self.repository.get_comments_for_post(post_slug)

        # Populate caches
        await self.redis_client.setex(
            cache_key,
            300,  # 5 minutes TTL
            json.dumps([c.dict() for c in comments])
        )
        self.local_cache[cache_key] = comments

        return comments

    async def invalidate_post_comments(self, post_slug: str):
        """Invalidate caches when new comments approved"""
        cache_key = f"comments:{post_slug}"

        # Clear from both cache levels
        self.local_cache.pop(cache_key, None)
        await self.redis_client.delete(cache_key)

    @lru_cache(maxsize=1000)
    def get_moderation_template(self, template_name: str) -> str:
        """Cache moderation email templates"""
        return self._load_template(template_name)
```

#### Cache Invalidation Strategy
```python
class CacheInvalidationService:
    async def handle_comment_approved(self, comment: Comment):
        """Invalidate relevant caches when comment approved"""

        # Invalidate post comment cache
        await self.cache_service.invalidate_post_comments(comment.post_slug)

        # Invalidate comment count cache
        await self.cache_service.invalidate_comment_count(comment.post_slug)

        # Update recent comments cache
        await self.cache_service.refresh_recent_comments()

    async def handle_gdpr_erasure(self, comment_ids: List[str]):
        """Handle cache invalidation for GDPR erasure"""

        affected_posts = await self.get_affected_posts(comment_ids)

        # Invalidate all affected post caches
        for post_slug in affected_posts:
            await self.cache_service.invalidate_post_comments(post_slug)
```

### 3. Content Delivery Optimization

#### Comment Rendering Pipeline
```python
class CommentRenderingService:
    async def render_comment_thread(
        self,
        post_slug: str,
        user_context: Optional[UserContext] = None
    ) -> str:
        """
        Optimized comment thread rendering with caching
        """
        # Check for cached rendered HTML
        cache_key = f"rendered_comments:{post_slug}"
        cached_html = await self.cache_service.get_rendered_html(cache_key)

        if cached_html and not self._requires_personalization(user_context):
            return cached_html

        # Fetch comments (potentially from cache)
        comments = await self.comment_service.get_post_comments(post_slug)

        # Build comment tree structure
        comment_tree = self._build_comment_tree(comments)

        # Render template with optimizations
        html = await self._render_template_optimized(
            "comments/thread.html",
            {
                "comments": comment_tree,
                "post_slug": post_slug,
                "user_context": user_context
            }
        )

        # Cache rendered HTML if not personalized
        if not self._requires_personalization(user_context):
            await self.cache_service.set_rendered_html(
                cache_key,
                html,
                ttl=300  # 5 minutes
            )

        return html

    def _build_comment_tree(self, comments: List[Comment]) -> CommentTree:
        """Efficiently build nested comment structure"""
        # Use dictionary for O(1) parent lookups
        comment_map = {c.id: c for c in comments}
        root_comments = []

        for comment in comments:
            if comment.parent_id and comment.parent_id in comment_map:
                parent = comment_map[comment.parent_id]
                parent.replies = parent.replies or []
                parent.replies.append(comment)
            else:
                root_comments.append(comment)

        return CommentTree(root_comments)
```

### 4. GDPR Performance Optimization

#### Data Access Request Optimization
```python
class GDPRPerformanceService:
    async def export_user_data_optimized(
        self,
        user_identifier: str
    ) -> DataExportPackage:
        """
        Optimized data export for GDPR access requests
        """
        # Use parallel queries for different data types
        async with asyncio.TaskGroup() as tg:
            comments_task = tg.create_task(
                self._export_user_comments(user_identifier)
            )
            personal_data_task = tg.create_task(
                self._export_personal_data(user_identifier)
            )
            consent_task = tg.create_task(
                self._export_consent_history(user_identifier)
            )
            audit_task = tg.create_task(
                self._export_audit_logs(user_identifier)
            )

        # Combine results efficiently
        export_package = DataExportPackage(
            user_identifier=user_identifier,
            export_date=datetime.utcnow(),
            comments=comments_task.result(),
            personal_data=personal_data_task.result(),
            consent_history=consent_task.result(),
            audit_logs=audit_task.result()
        )

        return export_package

    async def batch_erasure_processing(
        self,
        user_identifier: str
    ) -> ErasureResult:
        """
        Optimized batch processing for data erasure
        """
        # Process erasure in optimized batches
        batch_size = 100

        # Soft delete comments in batches
        comment_ids = await self._get_user_comment_ids(user_identifier)

        for i in range(0, len(comment_ids), batch_size):
            batch = comment_ids[i:i + batch_size]
            await self._batch_soft_delete_comments(batch)

            # Small delay to prevent database overload
            await asyncio.sleep(0.1)

        # Hard delete personal data (smaller dataset)
        await self._delete_personal_data(user_identifier)

        # Update audit logs
        await self._log_batch_erasure(user_identifier, len(comment_ids))

        return ErasureResult(
            success=True,
            items_erased=len(comment_ids),
            completion_date=datetime.utcnow()
        )
```

## 📊 Performance Monitoring

### 1. Application Metrics

#### Comment System Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Performance counters
comment_submissions = Counter(
    'comment_submissions_total',
    'Total comment submissions',
    ['status', 'post_slug']
)

comment_processing_time = Histogram(
    'comment_processing_seconds',
    'Time spent processing comments',
    ['operation']
)

moderation_queue_size = Gauge(
    'moderation_queue_size',
    'Current size of moderation queue'
)

gdpr_request_processing_time = Histogram(
    'gdpr_request_processing_seconds',
    'Time spent processing GDPR requests',
    ['request_type']
)

class CommentMetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        # Record metrics
        if request.url.path.startswith('/api/comments'):
            processing_time = time.time() - start_time
            comment_processing_time.labels(
                operation=request.method.lower()
            ).observe(processing_time)

        return response
```

#### Database Performance Monitoring
```python
class DatabaseMetricsCollector:
    async def collect_query_metrics(self):
        """Collect database performance metrics"""

        # Query execution times
        slow_queries = await self.get_slow_queries()
        for query in slow_queries:
            if query.duration > 1.0:  # Queries > 1 second
                logger.warning(f"Slow query detected: {query.sql[:100]}... "
                             f"Duration: {query.duration}s")

        # Index usage statistics
        index_stats = await self.get_index_usage_stats()
        for stat in index_stats:
            if stat.usage_ratio < 0.1:  # Unused indexes
                logger.info(f"Potentially unused index: {stat.index_name}")

        # Connection pool metrics
        pool_stats = await self.get_connection_pool_stats()
        if pool_stats.active_connections > pool_stats.max_connections * 0.8:
            logger.warning("Database connection pool near capacity")
```

### 2. User Experience Monitoring

#### Real User Monitoring (RUM)
```javascript
// Frontend performance tracking
class CommentPerformanceTracker {
    trackCommentSubmission() {
        const startTime = performance.now();

        fetch('/api/comments', {
            method: 'POST',
            body: formData
        }).then(response => {
            const endTime = performance.now();
            const duration = endTime - startTime;

            // Send metrics to monitoring service
            this.sendMetric('comment_submission_duration', duration, {
                status: response.status,
                user_agent: navigator.userAgent
            });

            if (duration > 2000) {
                this.sendAlert('slow_comment_submission', {
                    duration: duration,
                    url: window.location.href
                });
            }
        });
    }

    trackCommentLoad() {
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.name.includes('comments')) {
                    this.sendMetric('comment_load_duration', entry.duration);
                }
            }
        });

        observer.observe({entryTypes: ['resource']});
    }
}
```

## 🧪 Performance Testing

### Load Testing Strategy
```python
# Using locust for load testing
from locust import HttpUser, task, between
import random

class CommentSystemUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """Setup test user data"""
        self.post_slugs = [
            "test-post-1", "test-post-2", "test-post-3"
        ]
        self.test_comments = [
            "Great article!",
            "This is very helpful, thank you.",
            "I disagree with this point...",
            "Can you explain more about X?"
        ]

    @task(3)
    def view_comments(self):
        """Test comment viewing performance"""
        post_slug = random.choice(self.post_slugs)
        self.client.get(f"/api/comments/{post_slug}")

    @task(1)
    def submit_comment(self):
        """Test comment submission performance"""
        comment_data = {
            "content": random.choice(self.test_comments),
            "post_slug": random.choice(self.post_slugs),
            "agree_to_comment_storage": True,
            "allow_email_notifications": random.choice([True, False])
        }

        with self.client.post(
            "/api/comments",
            json=comment_data,
            catch_response=True
        ) as response:
            if response.status_code != 201:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def view_moderation_queue(self):
        """Test moderation interface performance"""
        self.client.get("/admin/moderation/queue")
```

### Stress Testing
```python
class CommentStressTest:
    async def test_concurrent_submissions(self):
        """Test system under high concurrent comment load"""

        async def submit_comment():
            async with aiohttp.ClientSession() as session:
                data = self.generate_test_comment()
                async with session.post('/api/comments', json=data) as resp:
                    return resp.status

        # Simulate 100 concurrent comment submissions
        tasks = [submit_comment() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r == 201)
        success_rate = success_count / len(results)

        assert success_rate > 0.95, f"Success rate too low: {success_rate}"

    async def test_gdpr_request_load(self):
        """Test GDPR request processing under load"""

        # Simulate multiple simultaneous GDPR requests
        user_identifiers = [f"user_{i}@example.com" for i in range(50)]

        async def process_gdpr_request(user_id):
            start_time = time.time()
            result = await self.gdpr_service.handle_data_access_request(user_id)
            processing_time = time.time() - start_time
            return processing_time

        tasks = [process_gdpr_request(uid) for uid in user_identifiers]
        processing_times = await asyncio.gather(*tasks)

        average_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)

        assert average_time < 5.0, f"Average processing time too high: {average_time}s"
        assert max_time < 10.0, f"Maximum processing time too high: {max_time}s"
```

## 🎯 Performance Budget

### Response Time Budget
- **Comment Form Load**: < 500ms
- **Comment Submission**: < 1000ms
- **Comment Thread Display**: < 750ms
- **Moderation Action**: < 300ms
- **GDPR Data Export**: < 5000ms

### Resource Budget
- **Database Connections**: < 80% of pool capacity
- **Memory Usage**: < 85% of available memory
- **CPU Usage**: < 70% average under normal load
- **Cache Hit Rate**: > 85% for comment reads

### Scalability Targets
- **Users**: Support 1000 concurrent comment readers
- **Submissions**: Handle 200 comments/minute sustained
- **Storage**: Efficient with 1M+ comments stored
- **GDPR Requests**: Process 100 requests/day efficiently

---

**Related Documentation**:
- [Architecture Decisions](architecture.md)
- [Implementation Details](implementation.md)
- [API Design](api-design.md)