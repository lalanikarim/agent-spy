# Agent Spy - Backend API Documentation

## Overview

The Agent Spy backend is built with FastAPI and provides a comprehensive REST API for trace ingestion, querying, and dashboard functionality. It maintains compatibility with LangSmith's API while extending functionality for advanced observability features.

## Architecture

### FastAPI Application Structure
```
src/
├── main.py              # Application entry point and configuration
├── api/                 # API route handlers
│   ├── health.py        # Health check endpoints
│   └── runs.py          # Trace/run management endpoints
├── core/                # Core infrastructure
│   ├── config.py        # Configuration management
│   ├── database.py      # Database connection and session management
│   └── logging.py       # Logging configuration
├── models/              # SQLAlchemy database models
│   ├── base.py          # Base model classes and mixins
│   ├── runs.py          # Run/trace database model
│   └── feedback.py      # Feedback database model
├── repositories/        # Data access layer
│   ├── runs.py          # Run repository with business logic
│   └── feedback.py      # Feedback repository
├── schemas/             # Pydantic models for API
│   ├── runs.py          # Run-related schemas
│   ├── dashboard.py     # Dashboard-specific schemas
│   └── feedback.py      # Feedback schemas
└── services/            # Business logic layer (planned)
```

## Configuration System

### Settings Management (`src/core/config.py`)

Agent Spy uses Pydantic Settings for comprehensive configuration management with environment variable support:

```python
class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Agent Spy"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./agentspy.db"
    database_pool_size: int = 20
    database_echo: bool = False
    
    # API Settings
    api_prefix: str = "/api/v1"
    require_auth: bool = False
    api_keys: list[str] | None = None
    
    # CORS Settings
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    
    # Performance Settings
    max_trace_size_mb: int = 10
    request_timeout: int = 30
    
    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "json"
```

### Environment Variables
All settings can be configured via environment variables:
```bash
# Application
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./agentspy.db
DATABASE_ECHO=false

# API
API_PREFIX=/api/v1
REQUIRE_AUTH=false
API_KEYS=key1,key2,key3

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_CREDENTIALS=true

# Performance
MAX_TRACE_SIZE_MB=10
REQUEST_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Database Layer

### SQLAlchemy Models

#### Base Model (`src/models/base.py`)
```python
class Base(DeclarativeBase):
    """Base class for all database models."""
    
class TimestampMixin:
    """Mixin for automatic timestamp management."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class ProjectMixin:
    """Mixin for project-related fields."""
    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
```

#### Run Model (`src/models/runs.py`)
```python
class Run(Base, TimestampMixin, ProjectMixin):
    __tablename__ = "runs"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, index=True)
    
    # Basic run information
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Timing information
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Hierarchy
    parent_run_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    
    # Data fields (JSON)
    inputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    outputs: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    serialized: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    events: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    
    # Error and status
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running", index=True)
    
    # Tags and references
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reference_example_id: Mapped[UUID | None] = mapped_column(GUID(), nullable=True, index=True)
```

### Database Indexes
Optimized indexes for common query patterns:
```python
__table_args__ = (
    Index("idx_runs_parent_start", "parent_run_id", "start_time"),
    Index("idx_runs_project_time", "project_name", "start_time"),
    Index("idx_runs_type_time", "run_type", "start_time"),
    Index("idx_runs_status_time", "status", "start_time"),
)
```

### Repository Pattern (`src/repositories/runs.py`)

The repository pattern provides a clean abstraction over database operations:

```python
class RunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, run_data: RunCreate) -> Run:
        """Create a new run."""
        
    async def update(self, run_id: UUID, run_data: RunUpdate) -> Run | None:
        """Update an existing run."""
        
    async def get_by_id(self, run_id: UUID) -> Run | None:
        """Get a run by ID."""
        
    async def get_root_runs(self, filters: TraceFilters, pagination: PaginationParams) -> RootRunsResponse:
        """Get root runs with filtering and pagination."""
        
    async def get_run_hierarchy(self, run_id: UUID) -> RunHierarchyResponse:
        """Get complete run hierarchy starting from a root run."""
        
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get statistics for dashboard."""
```

## API Endpoints

### Health Check Endpoints (`/health`)

#### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0",
  "environment": "production",
  "uptime_seconds": 3600.0,
  "database_status": "healthy",
  "dependencies": {
    "database": "healthy"
  }
}
```

#### Readiness Check
```http
GET /health/ready
```

**Response:**
```json
{
  "ready": true,
  "checks": {
    "application": true,
    "database": true,
    "configuration": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Liveness Check
```http
GET /health/live
```

**Response:**
```json
{
  "status": "alive",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### LangSmith Compatible Endpoints (`/api/v1`)

#### Service Information
```http
GET /api/v1/info
```

**Response:**
```json
{
  "version": "0.1.0",
  "license_expiration_time": null,
  "batch_ingest_config": {
    "size_limit": 20971520,
    "size_limit_bytes": 20971520,
    "scale_up_qsize_trigger": 1000,
    "scale_up_nthreads_limit": 16,
    "scale_down_nempty_trigger": 4
  },
  "tenant_handle": "agent-spy-local"
}
```

#### Batch Trace Ingestion
```http
POST /api/v1/runs/batch
Content-Type: application/json
```

**Request:**
```json
{
  "post": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Agent Planning",
      "run_type": "chain",
      "start_time": "2024-01-15T10:30:00Z",
      "inputs": {"query": "Analyze market trends"},
      "project_name": "market-analysis"
    }
  ],
  "patch": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "end_time": "2024-01-15T10:30:05Z",
      "outputs": {"result": "Market analysis complete"},
      "status": "completed"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "created_count": 1,
  "updated_count": 1,
  "errors": []
}
```

#### Individual Run Operations
```http
# Create run
POST /api/v1/runs

# Update run
PATCH /api/v1/runs/{run_id}

# Get run
GET /api/v1/runs/{run_id}
```

### Dashboard API Endpoints (`/api/v1/dashboard`)

#### Get Root Runs
```http
GET /api/v1/dashboard/runs/roots?project=&status=&search=&limit=50&offset=0
```

**Query Parameters:**
- `project`: Filter by project name
- `status`: Filter by run status (running, completed, failed)
- `search`: Text search in run names
- `start_time_gte`: Filter runs after this timestamp
- `start_time_lte`: Filter runs before this timestamp
- `limit`: Number of results (default: 50, max: 1000)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "runs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Agent Planning",
      "run_type": "chain",
      "status": "completed",
      "start_time": "2024-01-15T10:30:00Z",
      "end_time": "2024-01-15T10:30:05Z",
      "duration_ms": 5000,
      "inputs": {"query": "Analyze market trends"},
      "outputs": {"result": "Market analysis complete"},
      "project_name": "market-analysis"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0,
  "has_more": false
}
```

#### Get Run Hierarchy
```http
GET /api/v1/dashboard/runs/{trace_id}/hierarchy
```

**Response:**
```json
{
  "root_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "hierarchy": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Agent Planning",
    "run_type": "chain",
    "status": "completed",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:30:05Z",
    "duration_ms": 5000,
    "children": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "LLM Call",
        "run_type": "llm",
        "status": "completed",
        "start_time": "2024-01-15T10:30:01Z",
        "end_time": "2024-01-15T10:30:03Z",
        "duration_ms": 2000,
        "children": []
      }
    ]
  },
  "total_runs": 2,
  "max_depth": 2
}
```

#### Get Dashboard Statistics
```http
GET /api/v1/dashboard/stats/summary
```

**Response:**
```json
{
  "stats": {
    "total_runs": 1500,
    "total_traces": 300,
    "recent_runs_24h": 50,
    "status_distribution": {
      "completed": 1200,
      "failed": 200,
      "running": 100
    },
    "run_type_distribution": {
      "chain": 800,
      "llm": 400,
      "tool": 200,
      "retrieval": 100
    },
    "project_distribution": {
      "market-analysis": 600,
      "customer-support": 500,
      "research": 400
    }
  },
  "recent_projects": [
    {
      "name": "market-analysis",
      "total_runs": 600,
      "total_traces": 120,
      "last_activity": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Data Models & Schemas

### Pydantic Schemas (`src/schemas/`)

#### Run Schemas (`runs.py`)
```python
class RunBase(BaseModel):
    """Base model for runs matching LangSmith RunBase schema."""
    name: str
    start_time: datetime
    run_type: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    id: UUID | None = Field(default_factory=uuid4)
    end_time: datetime | None = None
    outputs: dict[str, Any] | None = None
    error: str | None = None
    parent_run_id: UUID | None = None
    # ... additional fields

class RunCreate(RunBase):
    """Model for creating new runs."""
    id: UUID = Field(..., description="Run ID (required for LangSmith compatibility)")

class RunUpdate(BaseModel):
    """Model for updating existing runs."""
    id: UUID = Field(..., description="ID of the run to update")
    # All other fields optional for updates
    name: str | None = None
    end_time: datetime | None = None
    outputs: dict[str, Any] | None = None
    # ... additional fields

class RunResponse(RunBase):
    """Model for run responses with additional computed fields."""
    id: UUID = Field(..., description="Run ID")
    duration_ms: int | None = Field(None, description="Duration in milliseconds")
    status: str | None = Field(None, description="Run status")
    # ... additional computed fields
```

#### Dashboard Schemas (`dashboard.py`)
```python
class DashboardStats(BaseModel):
    """Dashboard statistics model."""
    total_runs: int
    total_traces: int
    recent_runs_24h: int
    status_distribution: dict[str, int]
    run_type_distribution: dict[str, int]
    project_distribution: dict[str, int]

class RunHierarchyNode(BaseModel):
    """Hierarchical run node for tree visualization."""
    id: str
    name: str
    run_type: str
    status: str
    start_time: str | None
    end_time: str | None
    duration_ms: int | None
    children: list["RunHierarchyNode"]

class RootRunsResponse(BaseModel):
    """Response for root runs query."""
    runs: list[TraceRun]
    total: int
    limit: int
    offset: int
    has_more: bool
```

## Smart Completion Detection

Agent Spy includes intelligent completion detection that automatically determines when runs are completed:

```python
def update_run_status(run: Run) -> str:
    """
    Automatically determine run status based on available data.
    
    Rules:
    - If end_time and outputs exist: completed
    - If end_time and error exist: failed  
    - Otherwise: running
    """
    if run.end_time:
        if run.error:
            return "failed"
        elif run.outputs:
            return "completed"
    return "running"
```

This works across all run types (tools, chains, prompts, parsers, etc.) without manual configuration.

## Error Handling

### Exception Handlers
```python
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
```

### Request Validation
All API endpoints use Pydantic models for automatic request validation:
- **Input Validation**: Automatic type checking and conversion
- **Response Validation**: Ensures consistent API responses
- **Error Messages**: Clear validation error messages

## Middleware

### CORS Middleware
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)
```

### Request ID Middleware
```python
@app.middleware("http")
async def add_request_id(request, call_next):
    """Add request ID to all requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

## Performance Optimizations

### Database Connection Management
- **Async SQLAlchemy**: Non-blocking database operations
- **Connection Pooling**: Efficient connection reuse
- **Session Management**: Proper session lifecycle management

### Query Optimization
- **Composite Indexes**: Optimized for common query patterns
- **Pagination**: Efficient large result set handling
- **Selective Loading**: Only load required fields

### Response Caching (Planned)
- **Dashboard Statistics**: Cache frequently accessed stats
- **Query Results**: Cache common query results
- **ETags**: HTTP caching for unchanged resources

## Security Features

### Input Validation
- **Pydantic Validation**: Comprehensive input validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Input sanitization

### Authentication (Planned)
```python
# API Key authentication
async def verify_api_key(api_key: str = Header(...)):
    if settings.require_auth:
        if not settings.api_keys or api_key not in settings.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

### CORS Security
- **Origin Validation**: Configurable allowed origins
- **Credential Handling**: Secure credential policies
- **Method Restrictions**: Limited HTTP methods

## Logging & Monitoring

### Structured Logging
```python
# JSON logging for production
logger.info("Trace ingested", extra={
    "run_id": str(run.id),
    "run_type": run.run_type,
    "project": run.project_name,
    "duration_ms": duration_ms
})
```

### Request Tracing
- **Request IDs**: Unique identifier for each request
- **Correlation**: Link related log entries
- **Performance Metrics**: Request duration tracking

### Health Monitoring
- **Database Connectivity**: Monitor database health
- **Application Status**: Track application state
- **Resource Usage**: Monitor memory and CPU usage (planned)
