# Integration Patterns

**Last Updated**: 2025-09-20

## 🎯 Overview

This document defines the integration patterns used throughout the GoNoGo platform to ensure consistent, secure, and GDPR-compliant communication between components. These patterns facilitate maintainable inter-service communication while preserving privacy and performance.

## 🔗 Integration Architecture

### Component Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│  Blog Service ←→ Comment Service ←→ User Service ←→ GDPR    │
│       ↓              ↓               ↓           Service    │
│  Content Store   Database       Auth Service      ↓        │
│       ↓              ↓               ↓         Audit Log   │
│  Git Repository  PostgreSQL     Session Store              │
└─────────────────────────────────────────────────────────────┘
```

### Integration Principles

1. **Privacy-First Integration**: All data exchange minimizes personal information
2. **Loose Coupling**: Services interact through well-defined interfaces
3. **Idempotent Operations**: Repeated operations produce same result
4. **Graceful Degradation**: System continues functioning when components fail
5. **Audit Trail**: All integration points logged for compliance

## 📡 Internal Communication Patterns

### 1. Service-to-Service Communication

#### Direct Function Calls (Monolithic Pattern)
```python
# Primary pattern for GoNoGo's monolithic architecture
class BlogService:
    def __init__(self, comment_service: CommentService, user_service: UserService):
        self.comment_service = comment_service
        self.user_service = user_service
        self.audit_logger = AuditLogger()

    async def get_post_with_comments(self, post_id: str, user_context: UserContext) -> BlogPostResponse:
        """Get blog post with associated comments (privacy-filtered)"""
        try:
            # Get post content
            post = await self.get_post(post_id)
            if not post:
                raise PostNotFound(post_id)

            # Get comments with privacy filtering
            comments = await self.comment_service.get_comments_for_post(
                post_id=post_id,
                user_context=user_context,
                privacy_level=self.determine_privacy_level(user_context)
            )

            # Audit access
            self.audit_logger.log_content_access(
                user_id_hash=user_context.anonymized_user_id,
                resource_type="blog_post",
                resource_id=post_id,
                additional_resources={"comments_count": len(comments)}
            )

            return BlogPostResponse(
                post=post,
                comments=comments,
                user_permissions=self.user_service.get_user_permissions(user_context)
            )

        except Exception as e:
            self.audit_logger.log_integration_error(
                source_service="blog_service",
                target_service="comment_service",
                operation="get_post_with_comments",
                error_type=type(e).__name__,
                user_context=user_context.anonymized_user_id
            )
            raise
```

#### Event-Driven Communication (Background Tasks)
```python
# For asynchronous operations that don't block user requests
class EventBus:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_logger = EventLogger()

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to events with privacy-safe logging"""
        self.subscribers[event_type].append(handler)
        self.event_logger.log_subscription(event_type, handler.__name__)

    async def publish(self, event: Event):
        """Publish event to all subscribers with audit trail"""
        self.event_logger.log_event_published(
            event_type=event.type,
            event_id=event.id,
            timestamp=event.timestamp,
            anonymized_data=event.get_anonymized_data()
        )

        for handler in self.subscribers[event.type]:
            try:
                await handler(event)
                self.event_logger.log_event_handled(event.id, handler.__name__, "success")
            except Exception as e:
                self.event_logger.log_event_handled(event.id, handler.__name__, "error", str(e))
                # Continue processing other handlers

# Usage example: Comment moderation workflow
class CommentModerationService:
    @subscribe("comment.created")
    async def handle_new_comment(self, event: CommentCreatedEvent):
        """Automatically moderate new comments"""
        comment = event.comment

        # Check for spam/inappropriate content
        moderation_result = await self.content_moderator.analyze(comment.content)

        if moderation_result.requires_review:
            await self.flag_for_manual_review(comment.id)
            await self.notify_moderators(comment.id)

        # GDPR: Log moderation action
        self.audit_logger.log_moderation_action(
            comment_id=comment.id,
            action="auto_moderation",
            result=moderation_result.status,
            anonymized_user_id=comment.author.anonymized_id
        )
```

### 2. Data Access Patterns

#### Repository Pattern with Privacy Layer
```python
class CommentRepository:
    def __init__(self, db: Database, privacy_filter: PrivacyFilter):
        self.db = db
        self.privacy_filter = privacy_filter

    async def get_comments_for_post(
        self,
        post_id: str,
        user_context: UserContext,
        privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    ) -> List[Comment]:
        """Get comments with automatic privacy filtering"""

        # Base query with privacy-aware joins
        query = select(Comment).where(
            Comment.post_id == post_id,
            Comment.moderation_status == ModerationStatus.APPROVED,
            Comment.is_deleted == False
        )

        # Apply privacy filtering based on user context
        if privacy_level == PrivacyLevel.PUBLIC:
            # Public view: anonymize all personal data
            query = query.options(
                selectinload(Comment.author).load_only("anonymized_id", "display_name")
            )
        elif privacy_level == PrivacyLevel.AUTHENTICATED:
            # Authenticated users: show more context but still protect privacy
            query = query.options(
                selectinload(Comment.author).load_only(
                    "anonymized_id", "display_name", "reputation_score"
                )
            )

        comments = await self.db.execute(query)
        return self.privacy_filter.filter_comment_list(comments.scalars().all(), user_context)

    async def create_comment(self, comment_data: CreateCommentRequest) -> Comment:
        """Create comment with full audit trail"""
        # Validate GDPR consent
        if not comment_data.gdpr_consent:
            raise GDPRConsentRequired()

        # Create comment with privacy-safe data storage
        comment = Comment(
            id=uuid4(),
            post_id=comment_data.post_id,
            content=self.sanitize_content(comment_data.content),
            author_name=comment_data.author_name,
            author_email_hash=self.hash_email(comment_data.author_email),  # Store hash only
            created_at=datetime.utcnow(),
            moderation_status=ModerationStatus.PENDING,
            gdpr_consent_timestamp=datetime.utcnow(),
            ip_address_hash=self.hash_ip(comment_data.ip_address),  # Anonymized IP
            retention_until=datetime.utcnow() + timedelta(days=2190)  # 6 years
        )

        await self.db.add(comment)
        await self.db.commit()

        # Trigger async moderation
        await self.event_bus.publish(CommentCreatedEvent(comment=comment))

        return comment
```

#### Unit of Work Pattern
```python
class UnitOfWork:
    """Manage database transactions across multiple repositories"""

    def __init__(self, session_factory: Callable):
        self.session_factory = session_factory
        self._session = None
        self._transaction_id = None

    async def __aenter__(self):
        self._session = self.session_factory()
        self._transaction_id = str(uuid4())
        await self._session.begin()

        # Audit transaction start
        self.audit_logger.log_transaction_start(
            transaction_id=self._transaction_id,
            timestamp=datetime.utcnow()
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self._session.commit()
                self.audit_logger.log_transaction_commit(self._transaction_id)
            else:
                await self._session.rollback()
                self.audit_logger.log_transaction_rollback(
                    self._transaction_id,
                    error_type=exc_type.__name__ if exc_type else None
                )
        finally:
            await self._session.close()

    # Repository property accessors with shared session
    @property
    def comments(self) -> CommentRepository:
        return CommentRepository(self._session)

    @property
    def users(self) -> UserRepository:
        return UserRepository(self._session)

# Usage example
async def approve_comment_with_notification(comment_id: UUID, moderator_id: UUID):
    """Approve comment and notify author - atomic operation"""
    async with UnitOfWork(session_factory) as uow:
        # Update comment status
        comment = await uow.comments.get_by_id(comment_id)
        comment.moderation_status = ModerationStatus.APPROVED
        comment.approved_by = moderator_id
        comment.approved_at = datetime.utcnow()

        # Log moderation action
        await uow.audit_logs.create(AuditLogEntry(
            action="comment_approved",
            resource_type="comment",
            resource_id=comment_id,
            moderator_id_hash=anonymize_user_id(moderator_id),
            timestamp=datetime.utcnow()
        ))

        # Send notification (if user consented)
        user = await uow.users.get_by_comment_id(comment_id)
        if user.email_notifications_enabled:
            await self.notification_service.send_comment_approved(
                user_email_hash=user.email_hash,
                comment_id=comment_id,
                post_title=comment.post.title
            )
```

## 🌐 External Integration Patterns

### 1. GitHub Integration

#### Git-Based Content Management
```python
class GitContentProvider:
    """Integrate with Git repository for content management"""

    def __init__(self, repo_path: Path, branch: str = "main"):
        self.repo_path = repo_path
        self.branch = branch
        self.git_client = GitClient()

    async def get_blog_posts(self) -> List[BlogPost]:
        """Load blog posts from Git repository with caching"""
        try:
            # Check for content updates
            latest_commit = await self.git_client.get_latest_commit(self.branch)
            cached_posts = await self.cache.get_posts(commit_hash=latest_commit.hash)

            if cached_posts:
                return cached_posts

            # Load and parse markdown files
            post_files = self.get_markdown_files(self.repo_path / "content" / "posts")
            posts = []

            for file_path in post_files:
                try:
                    post_content = await self.load_markdown_file(file_path)
                    post = await self.parse_blog_post(post_content, file_path)
                    posts.append(post)
                except Exception as e:
                    self.logger.error(f"Failed to load post {file_path}: {e}")
                    continue

            # Cache parsed posts
            await self.cache.store_posts(posts, commit_hash=latest_commit.hash)
            return posts

        except GitError as e:
            self.logger.error(f"Git integration error: {e}")
            # Fallback to cached content
            return await self.cache.get_posts(fallback=True)

    async def create_content_webhook(self) -> WebhookConfig:
        """Set up webhook for content updates"""
        webhook_config = WebhookConfig(
            url=f"{self.base_url}/webhooks/content-updated",
            events=["push", "pull_request"],
            secret=self.webhook_secret,
            content_type="application/json"
        )

        await self.github_client.create_webhook(
            owner=self.repo_owner,
            repo=self.repo_name,
            config=webhook_config
        )

        return webhook_config
```

#### Webhook Processing
```python
class ContentWebhookHandler:
    """Handle GitHub webhooks for content updates"""

    @webhook.handler("push")
    async def handle_content_push(self, payload: GitHubPushPayload):
        """Process content updates from Git push"""
        # Validate webhook signature
        if not self.validate_webhook_signature(payload):
            raise WebhookValidationError()

        # Check if content files were modified
        content_changes = self.extract_content_changes(payload.commits)
        if not content_changes:
            return  # No content updates

        # Audit webhook processing
        self.audit_logger.log_webhook_processed(
            webhook_type="github_push",
            repository=payload.repository.full_name,
            commit_hash=payload.head_commit.id,
            changes_count=len(content_changes)
        )

        # Invalidate content cache
        await self.cache.invalidate_content_cache()

        # Trigger content reprocessing
        await self.event_bus.publish(ContentUpdatedEvent(
            changes=content_changes,
            commit_hash=payload.head_commit.id,
            timestamp=datetime.utcnow()
        ))

        # Send deployment notification
        await self.notification_service.notify_content_updated(
            commit_message=payload.head_commit.message,
            author=payload.head_commit.author.name,
            changes_summary=self.summarize_changes(content_changes)
        )
```

### 2. DigitalOcean Platform Integration

#### App Platform Deployment Integration
```python
class DigitalOceanIntegration:
    """Integration with DigitalOcean App Platform"""

    def __init__(self, api_key: str, app_id: str):
        self.client = DigitalOceanClient(api_key)
        self.app_id = app_id

    async def deploy_application(self, deployment_config: DeploymentConfig) -> Deployment:
        """Deploy application with GDPR-compliant configuration"""
        # Ensure EU region deployment for GDPR compliance
        if deployment_config.region not in ['ams3', 'fra1']:
            raise InvalidRegionError("GDPR compliance requires EU region deployment")

        # Configure environment variables with security
        env_vars = {
            **deployment_config.environment_variables,
            'GDPR_COMPLIANCE_MODE': 'production',
            'DATA_REGION': 'EU',
            'LOG_LEVEL': 'INFO',
            'SECURITY_HEADERS_ENABLED': 'true'
        }

        # Deploy with monitoring
        deployment = await self.client.create_deployment(
            app_id=self.app_id,
            spec={
                'name': deployment_config.app_name,
                'region': deployment_config.region,
                'services': [{
                    'name': 'web',
                    'source_dir': '/',
                    'github': {
                        'repo': deployment_config.github_repo,
                        'branch': deployment_config.branch
                    },
                    'run_command': 'gunicorn src.be.main:app -w 4 -k uvicorn.workers.UvicornWorker',
                    'environment_slug': 'python',
                    'instance_count': deployment_config.instance_count,
                    'instance_size_slug': deployment_config.instance_size,
                    'envs': [{'key': k, 'value': v} for k, v in env_vars.items()]
                }]
            }
        )

        # Audit deployment
        self.audit_logger.log_deployment(
            deployment_id=deployment.id,
            app_id=self.app_id,
            region=deployment_config.region,
            instance_count=deployment_config.instance_count,
            timestamp=datetime.utcnow()
        )

        return deployment

    async def get_application_metrics(self, time_range: str = "1h") -> AppMetrics:
        """Get application performance metrics"""
        metrics = await self.client.get_app_metrics(
            app_id=self.app_id,
            time_range=time_range
        )

        # Privacy-safe metrics processing
        return AppMetrics(
            cpu_usage=metrics.cpu_usage,
            memory_usage=metrics.memory_usage,
            request_count=metrics.request_count,
            response_time_avg=metrics.response_time_avg,
            error_rate=metrics.error_rate,
            timestamp=datetime.utcnow(),
            region=metrics.region
        )
```

### 3. Email Service Integration

#### Transactional Email with Privacy Protection
```python
class EmailService:
    """GDPR-compliant email service integration"""

    def __init__(self, provider: EmailProvider):
        self.provider = provider
        self.template_cache = TemplateCache()

    async def send_comment_notification(
        self,
        recipient_email_hash: str,
        comment_data: CommentNotificationData
    ) -> EmailDeliveryResult:
        """Send comment notification with privacy protection"""

        # Check user email preferences and consent
        user_preferences = await self.get_user_email_preferences(recipient_email_hash)
        if not user_preferences.comment_notifications_enabled:
            return EmailDeliveryResult(status="skipped", reason="user_preferences")

        # Validate GDPR consent for email communications
        if not user_preferences.email_consent_given:
            return EmailDeliveryResult(status="skipped", reason="no_consent")

        # Load email template with privacy-safe data
        template = await self.template_cache.get_template("comment_notification")
        email_content = template.render(
            post_title=comment_data.post_title,
            comment_preview=self.truncate_content(comment_data.comment_content, 100),
            post_url=comment_data.post_url,
            unsubscribe_url=self.generate_unsubscribe_url(recipient_email_hash),
            privacy_policy_url=f"{self.base_url}/privacy-policy"
        )

        # Send email with audit trail
        try:
            delivery_result = await self.provider.send_email(
                to=self.resolve_email_from_hash(recipient_email_hash),
                subject=f"New comment on: {comment_data.post_title}",
                html_content=email_content,
                tracking_disabled=True,  # Privacy-first: no email tracking
                list_unsubscribe_header=self.generate_unsubscribe_url(recipient_email_hash)
            )

            # Audit email sent (privacy-safe logging)
            self.audit_logger.log_email_sent(
                email_type="comment_notification",
                recipient_hash=recipient_email_hash,
                delivery_id=delivery_result.id,
                status=delivery_result.status,
                timestamp=datetime.utcnow()
            )

            return delivery_result

        except EmailDeliveryError as e:
            self.audit_logger.log_email_error(
                email_type="comment_notification",
                recipient_hash=recipient_email_hash,
                error=str(e),
                timestamp=datetime.utcnow()
            )
            raise
```

## 🔄 Data Flow Patterns

### 1. Request-Response Flow

#### GDPR-Compliant Request Processing
```python
class RequestProcessingPipeline:
    """Process requests with privacy and security at each stage"""

    def __init__(self):
        self.middleware_stack = [
            SecurityHeadersMiddleware(),
            RateLimitingMiddleware(),
            GDPRComplianceMiddleware(),
            AuditLoggingMiddleware(),
            ValidationMiddleware(),
            AuthenticationMiddleware(),
            AuthorizationMiddleware()
        ]

    async def process_request(self, request: Request) -> Response:
        """Process request through privacy-aware middleware stack"""
        context = RequestContext(
            request_id=str(uuid4()),
            start_time=datetime.utcnow(),
            ip_hash=self.anonymize_ip(request.client.host),
            user_agent_hash=self.anonymize_user_agent(request.headers.get('user-agent'))
        )

        try:
            # Process through middleware stack
            for middleware in self.middleware_stack:
                request = await middleware.process_request(request, context)

            # Handle business logic
            response = await self.route_handler(request, context)

            # Process response through middleware (reverse order)
            for middleware in reversed(self.middleware_stack):
                response = await middleware.process_response(response, context)

            # Audit successful request
            self.audit_logger.log_request_completed(
                request_id=context.request_id,
                method=request.method,
                path_template=self.get_path_template(request.url.path),
                status_code=response.status_code,
                duration_ms=self.calculate_duration(context.start_time),
                user_id_hash=context.user_id_hash
            )

            return response

        except Exception as e:
            # Audit request error
            self.audit_logger.log_request_error(
                request_id=context.request_id,
                error_type=type(e).__name__,
                error_message=str(e),
                user_id_hash=context.user_id_hash
            )
            raise
```

### 2. Event-Driven Data Flow

#### Privacy-Safe Event Processing
```python
class PrivacyAwareEventProcessor:
    """Process events while maintaining privacy compliance"""

    async def process_user_action_event(self, event: UserActionEvent):
        """Process user action with privacy protection"""

        # Anonymize event data immediately
        anonymized_event = AnonymizedEvent(
            event_id=event.id,
            event_type=event.type,
            timestamp=event.timestamp,
            user_id_hash=self.anonymize_user_id(event.user_id),
            action_data=self.filter_sensitive_data(event.action_data),
            ip_hash=self.anonymize_ip(event.ip_address),
            session_hash=self.anonymize_session_id(event.session_id)
        )

        # Store for analytics (privacy-compliant)
        await self.analytics_store.store_event(anonymized_event)

        # Trigger business logic handlers
        for handler in self.get_handlers(event.type):
            try:
                await handler.process(anonymized_event)
            except Exception as e:
                self.error_logger.log_handler_error(
                    event_id=anonymized_event.event_id,
                    handler_name=handler.__class__.__name__,
                    error=str(e)
                )

        # Schedule data retention cleanup
        await self.schedule_data_cleanup(anonymized_event)
```

## 📊 Integration Monitoring & Health Checks

### Health Check Framework
```python
class IntegrationHealthMonitor:
    """Monitor health of all integration points"""

    def __init__(self):
        self.health_checks = [
            DatabaseHealthCheck(),
            GitRepositoryHealthCheck(),
            EmailServiceHealthCheck(),
            DigitalOceanAPIHealthCheck(),
            CacheHealthCheck()
        ]

    async def check_system_health(self) -> SystemHealthReport:
        """Comprehensive health check of all integrations"""
        health_results = {}

        for health_check in self.health_checks:
            try:
                start_time = time.time()
                result = await health_check.check()
                duration = time.time() - start_time

                health_results[health_check.name] = HealthCheckResult(
                    status=result.status,
                    response_time_ms=round(duration * 1000, 2),
                    details=result.details,
                    timestamp=datetime.utcnow()
                )

            except Exception as e:
                health_results[health_check.name] = HealthCheckResult(
                    status="unhealthy",
                    error=str(e),
                    timestamp=datetime.utcnow()
                )

        # Determine overall system health
        overall_status = self.calculate_overall_health(health_results)

        return SystemHealthReport(
            overall_status=overall_status,
            component_health=health_results,
            timestamp=datetime.utcnow()
        )

# Individual health check implementations
class DatabaseHealthCheck:
    async def check(self) -> HealthResult:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            await self.db.execute(text("SELECT 1"))
            query_time = time.time() - start_time

            return HealthResult(
                status="healthy" if query_time < 0.1 else "degraded",
                details={
                    "query_response_time": f"{query_time:.3f}s",
                    "connection_pool": self.db.pool.status()
                }
            )
        except Exception as e:
            return HealthResult(status="unhealthy", error=str(e))
```

---

**Pattern Evolution**: These integration patterns will evolve as the system scales and new requirements emerge.

**Security Integration**: All patterns integrate with the security architecture defined in `security-architecture.md`.