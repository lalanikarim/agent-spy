# Agent Spy - API Reference

## Overview

Agent Spy provides a comprehensive REST API for trace ingestion, querying, and dashboard functionality. The API is designed to be compatible with LangSmith's API while extending functionality for advanced observability features.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configure via environment variables
- **API Base Path**: `/api/v1`

## Authentication

Currently, Agent Spy supports optional API key authentication:

```bash
# Set API keys in environment
API_KEYS=key1,key2,key3
REQUIRE_AUTH=true
```

When authentication is enabled, include the API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/v1/dashboard/runs/roots
```

## Common Headers

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer your-api-key  # Optional
```

## Response Format

All API responses follow a consistent format:

```json
{
  "data": {
    // Response data
  },
  "message": "Success message",
  "status": "success"
}
```

Error responses:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Health Endpoints

### GET /health

Basic health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "0.1.0"
}
```

### GET /health/ready

Readiness probe for container orchestration.

**Response:**

```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### GET /health/live

Liveness probe for container orchestration.

**Response:**

```json
{
  "status": "alive",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Service Information

### GET /api/v1/info

Get service information for LangSmith compatibility.

**Response:**

```json
{
  "version": "0.1.0",
  "license_expiration_time": null,
  "tenant_handle": "agent-spy-local"
}
```

## Trace Management

### POST /api/v1/runs/batch

Batch ingest runs (traces and spans). This is the main endpoint that LangChain uses to send trace data.

**Request Body:**

```json
{
  "post": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Agent Planning Session",
      "run_type": "chain",
      "start_time": "2024-01-01T12:00:00Z",
      "end_time": "2024-01-01T12:01:00Z",
      "inputs": {
        "query": "Analyze market trends"
      },
      "outputs": {
        "result": "Market analysis completed"
      },
      "project_name": "market-analysis",
      "status": "completed",
      "parent_run_id": null,
      "extra": {
        "metadata": "Additional information"
      },
      "tags": ["analysis", "market"]
    }
  ],
  "patch": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "end_time": "2024-01-01T12:01:00Z",
      "outputs": {
        "result": "Updated result"
      },
      "status": "completed"
    }
  ]
}
```

**Response:**

```json
{
  "post": {
    "ids": ["550e8400-e29b-41d4-a716-446655440000"]
  },
  "patch": {
    "ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }
}
```

### POST /api/v1/runs

Create a single run.

**Request Body:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LLM Call",
  "run_type": "llm",
  "start_time": "2024-01-01T12:00:00Z",
  "inputs": {
    "prompt": "What is the weather like?"
  },
  "project_name": "weather-app"
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LLM Call",
  "run_type": "llm",
  "start_time": "2024-01-01T12:00:00Z",
  "status": "running",
  "project_name": "weather-app"
}
```

### PATCH /api/v1/runs/{run_id}

Update an existing run.

**Request Body:**

```json
{
  "end_time": "2024-01-01T12:01:00Z",
  "outputs": {
    "response": "The weather is sunny"
  },
  "status": "completed"
}
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LLM Call",
  "run_type": "llm",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T12:01:00Z",
  "status": "completed",
  "project_name": "weather-app"
}
```

### GET /api/v1/runs/{run_id}

Get a specific run by ID.

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LLM Call",
  "run_type": "llm",
  "start_time": "2024-01-01T12:00:00Z",
  "end_time": "2024-01-01T12:01:00Z",
  "parent_run_id": null,
  "inputs": {
    "prompt": "What is the weather like?"
  },
  "outputs": {
    "response": "The weather is sunny"
  },
  "extra": {},
  "serialized": {},
  "events": [],
  "error": null,
  "tags": [],
  "reference_example_id": null,
  "status": "completed",
  "project_name": "weather-app",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:01:00Z"
}
```

## Dashboard API

### GET /api/v1/dashboard/runs/roots

Get root traces (traces without parent runs) with filtering and pagination.

**Query Parameters:**

- `project` (string, optional): Filter by project name
- `status` (string, optional): Filter by status (running, completed, failed)
- `search` (string, optional): Search in trace names and content
- `limit` (integer, optional): Number of results to return (default: 50, max: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/dashboard/runs/roots?project=market-analysis&status=completed&limit=20"
```

**Response:**

```json
{
  "runs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Agent Planning Session",
      "run_type": "chain",
      "start_time": "2024-01-01T12:00:00Z",
      "end_time": "2024-01-01T12:01:00Z",
      "status": "completed",
      "project_name": "market-analysis",
      "child_run_count": 5,
      "duration_seconds": 60.0
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### GET /api/v1/dashboard/runs/{run_id}/hierarchy

Get the complete hierarchy of a run, including all child runs.

**Response:**

```json
{
  "run": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Agent Planning Session",
    "run_type": "chain",
    "start_time": "2024-01-01T12:00:00Z",
    "end_time": "2024-01-01T12:01:00Z",
    "status": "completed",
    "project_name": "market-analysis"
  },
  "children": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "LLM Call",
      "run_type": "llm",
      "start_time": "2024-01-01T12:00:10Z",
      "end_time": "2024-01-01T12:00:30Z",
      "status": "completed",
      "parent_run_id": "550e8400-e29b-41d4-a716-446655440000",
      "children": []
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Tool Call",
      "run_type": "tool",
      "start_time": "2024-01-01T12:00:35Z",
      "end_time": "2024-01-01T12:00:45Z",
      "status": "completed",
      "parent_run_id": "550e8400-e29b-41d4-a716-446655440000",
      "children": []
    }
  ]
}
```

### GET /api/v1/dashboard/stats/summary

Get summary statistics for the dashboard.

**Response:**

```json
{
  "total_runs": 150,
  "completed_runs": 120,
  "running_runs": 5,
  "failed_runs": 25,
  "projects": [
    {
      "name": "market-analysis",
      "run_count": 50,
      "completed_count": 45,
      "failed_count": 5
    },
    {
      "name": "weather-app",
      "run_count": 100,
      "completed_count": 75,
      "failed_count": 20
    }
  ],
  "run_types": [
    {
      "type": "chain",
      "count": 80
    },
    {
      "type": "llm",
      "count": 50
    },
    {
      "type": "tool",
      "count": 20
    }
  ],
  "recent_activity": {
    "last_24_hours": 25,
    "last_hour": 3
  }
}
```

## Feedback API

### POST /api/v1/feedback

Create feedback for a run.

**Request Body:**

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "user_satisfaction",
  "score": 4.5,
  "comment": "Good response quality",
  "correction": null,
  "metadata": {
    "user_id": "user123"
  }
}
```

**Response:**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "user_satisfaction",
  "score": 4.5,
  "comment": "Good response quality",
  "correction": null,
  "metadata": {
    "user_id": "user123"
  },
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /api/v1/feedback/{run_id}

Get feedback for a specific run.

**Response:**

```json
{
  "feedback": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "key": "user_satisfaction",
      "score": 4.5,
      "comment": "Good response quality",
      "correction": null,
      "metadata": {
        "user_id": "user123"
      },
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

## Data Models

### Run Model

```json
{
  "id": "string (UUID)",
  "name": "string",
  "run_type": "string (chain|llm|tool|retrieval|prompt|parser|embedding|custom)",
  "start_time": "string (ISO 8601)",
  "end_time": "string (ISO 8601) | null",
  "parent_run_id": "string (UUID) | null",
  "inputs": "object | null",
  "outputs": "object | null",
  "extra": "object | null",
  "serialized": "object | null",
  "events": "array | null",
  "error": "string | null",
  "tags": "array[string] | null",
  "reference_example_id": "string (UUID) | null",
  "status": "string (running|completed|failed)",
  "project_name": "string",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### Feedback Model

```json
{
  "id": "string (UUID)",
  "run_id": "string (UUID)",
  "key": "string",
  "score": "number | null",
  "comment": "string | null",
  "correction": "string | null",
  "metadata": "object | null",
  "created_at": "string (ISO 8601)"
}
```

## Error Codes

| Status Code | Description                             |
| ----------- | --------------------------------------- |
| 200         | Success                                 |
| 201         | Created                                 |
| 400         | Bad Request - Invalid input data        |
| 401         | Unauthorized - Authentication required  |
| 403         | Forbidden - Insufficient permissions    |
| 404         | Not Found - Resource not found          |
| 422         | Unprocessable Entity - Validation error |
| 500         | Internal Server Error                   |

## Rate Limiting

Currently, Agent Spy does not implement rate limiting. This may be added in future versions for production deployments.

## Pagination

Endpoints that return lists support pagination using `limit` and `offset` parameters:

```bash
# Get first 20 results
GET /api/v1/dashboard/runs/roots?limit=20&offset=0

# Get next 20 results
GET /api/v1/dashboard/runs/roots?limit=20&offset=20
```

## Filtering

Several endpoints support filtering:

### Project Filtering

```bash
GET /api/v1/dashboard/runs/roots?project=my-project
```

### Status Filtering

```bash
GET /api/v1/dashboard/runs/roots?status=completed
GET /api/v1/dashboard/runs/roots?status=running
GET /api/v1/dashboard/runs/roots?status=failed
```

### Search

```bash
GET /api/v1/dashboard/runs/roots?search=market analysis
```

## Examples

### Complete Trace Ingestion Workflow

```python
import requests
import json
from datetime import datetime
from uuid import uuid4

# 1. Create a root trace
root_trace_id = str(uuid4())
root_trace = {
    "id": root_trace_id,
    "name": "Market Analysis Agent",
    "run_type": "chain",
    "start_time": datetime.now().isoformat(),
    "inputs": {"query": "Analyze market trends for tech stocks"},
    "project_name": "market-analysis",
    "status": "running"
}

# 2. Create child runs
llm_run_id = str(uuid4())
llm_run = {
    "id": llm_run_id,
    "name": "LLM Analysis",
    "run_type": "llm",
    "start_time": datetime.now().isoformat(),
    "parent_run_id": root_trace_id,
    "inputs": {"prompt": "Analyze the current tech market trends"},
    "project_name": "market-analysis",
    "status": "running"
}

# 3. Send initial batch
response = requests.post(
    "http://localhost:8000/api/v1/runs/batch",
    json={"post": [root_trace, llm_run], "patch": []}
)

# 4. Update with results
llm_update = {
    "id": llm_run_id,
    "end_time": datetime.now().isoformat(),
    "outputs": {"response": "Tech stocks are showing strong growth..."},
    "status": "completed"
}

root_update = {
    "id": root_trace_id,
    "end_time": datetime.now().isoformat(),
    "outputs": {"analysis": "Market analysis completed successfully"},
    "status": "completed"
}

# 5. Send updates
response = requests.post(
    "http://localhost:8000/api/v1/runs/batch",
    json={"post": [], "patch": [llm_update, root_update]}
)
```

### Dashboard Integration

```python
import requests

# Get root traces
response = requests.get("http://localhost:8000/api/v1/dashboard/runs/roots")
traces = response.json()["runs"]

# Get trace hierarchy
for trace in traces:
    hierarchy_response = requests.get(
        f"http://localhost:8000/api/v1/dashboard/runs/{trace['id']}/hierarchy"
    )
    hierarchy = hierarchy_response.json()
    print(f"Trace: {hierarchy['run']['name']}")
    print(f"Children: {len(hierarchy['children'])}")

# Get statistics
stats_response = requests.get("http://localhost:8000/api/v1/dashboard/stats/summary")
stats = stats_response.json()
print(f"Total runs: {stats['total_runs']}")
print(f"Completed: {stats['completed_runs']}")
```

## SDK Support

Agent Spy is designed to be compatible with LangSmith's Python SDK. You can use the LangSmith client by configuring it to point to Agent Spy:

```python
import os
from langsmith import Client

# Configure for Agent Spy
os.environ["LANGSMITH_ENDPOINT"] = "http://localhost:8000/api/v1"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"

# Use LangSmith client
client = Client()
```

## WebSocket Support

Currently, Agent Spy does not support WebSocket connections. Real-time updates are achieved through polling the dashboard endpoints.
