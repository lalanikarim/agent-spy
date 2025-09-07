# API Health Checks & Monitoring Documentation

## 📋 Overview

This document describes the comprehensive health check and monitoring endpoints implemented in Phase 4 of the trace output missing issue resolution. These endpoints provide proactive monitoring and early detection of trace completeness issues.

## 🏥 Health Check Endpoints

### **Base Health Check** `/health`

**Endpoint**: `GET /health`

**Purpose**: Basic application health status

**Response Model**: `HealthResponse`

```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-09-02T01:04:25.249Z",
  "version": "0.1.0",
  "environment": "development",
  "uptime_seconds": 3600.0,
  "database_status": "connected|disconnected",
  "database_type": "postgresql",
  "dependencies": {
    "database": "connected"
  }
}
```

**Status Levels**:

- **healthy**: All systems operational
- **degraded**: Some systems experiencing issues but functional
- **unhealthy**: Critical systems down

---

### **Readiness Check** `/health/ready`

**Endpoint**: `GET /health/ready`

**Purpose**: Determine if application is ready to serve requests

**Response Model**: `ReadinessResponse`

```json
{
  "ready": true,
  "checks": {
    "application": true,
    "database": true,
    "configuration": true
  },
  "timestamp": "2025-09-02T01:04:25.249Z"
}
```

**Use Case**: Kubernetes liveness/readiness probes, load balancer health checks

---

### **Liveness Check** `/health/live`

**Endpoint**: `GET /health/live`

**Purpose**: Simple check that application process is running

**Response**: Simple JSON response

```json
{
  "alive": true,
  "timestamp": "2025-09-02T01:04:25.249Z"
}
```

---

### **Trace Completeness Health Check** `/health/traces` ⭐ **NEW IN PHASE 4**

**Endpoint**: `GET /health/traces`

**Purpose**: Monitor trace completeness and detect missing outputs proactively

**Response**: Comprehensive trace health status

```json
{
  "status": "healthy|degraded|unhealthy",
  "completeness_score": 0.95,
  "total_traces_checked": 150,
  "critical_issues": [
    "2 traces marked completed but missing outputs",
    "1 potentially orphaned traces"
  ],
  "problematic_traces_count": 3,
  "timestamp": "2025-09-02T01:04:25.249Z",
  "details": {
    "completed_missing_outputs": 2,
    "long_running_potential_orphans": 1,
    "incomplete_completion": 0
  }
}
```

**Status Thresholds**:

- **healthy**: ≥95% completeness score
- **degraded**: 90-94% completeness score
- **unhealthy**: <90% completeness score

**Critical Issues Detected**:

- **completed_missing_outputs**: Traces marked as completed but missing outputs
- **long_running_potential_orphans**: Traces running for >2 hours (potential orphans)
- **incomplete_completion**: Traces with end_time but no outputs

---

## 🔍 Trace Completeness Monitoring

### **Repository Methods**

#### **`check_trace_completeness()`**

**Location**: `src/repositories/runs.py`

**Purpose**: Check for incomplete traces across all projects or specific project

**Parameters**:

- `project_name` (optional): Specific project to check
- `hours_back`: How many hours back to check (default: 24)

**Returns**: Comprehensive completeness statistics

```python
async def check_trace_completeness(
    self,
    project_name: str | None = None,
    hours_back: int = 24
) -> dict
```

**Example Usage**:

```python
# Check all projects for last 24 hours
stats = await run_repo.check_trace_completeness()

# Check specific project for last 48 hours
project_stats = await run_repo.check_trace_completeness(
    project_name="my-project",
    hours_back=48
)
```

#### **`get_trace_hierarchy_completeness()`**

**Location**: `src/repositories/runs.py`

**Purpose**: Check completeness of a specific trace hierarchy

**Parameters**:

- `root_trace_id`: ID of the root trace to analyze

**Returns**: Hierarchy-specific completeness information

```python
async def get_trace_hierarchy_completeness(
    self,
    root_trace_id: UUID
) -> dict
```

**Example Usage**:

```python
# Check specific trace hierarchy
hierarchy_stats = await run_repo.get_trace_hierarchy_completeness(
    root_trace_id=uuid.UUID("...")
)
```

---

## 📊 Monitoring & Alerting

### **Key Metrics to Track**

1. **Completeness Score**: Overall trace completeness percentage
2. **Critical Issues Count**: Number of problematic traces
3. **Missing Outputs**: Traces completed without outputs
4. **Orphaned Traces**: Long-running traces (>2 hours)
5. **Incomplete Completions**: Traces with end_time but no outputs

### **Recommended Alerting Rules**

#### **High Priority Alerts**

- **Completeness Score < 90%**: System experiencing significant issues
- **Critical Issues > 10**: Multiple problematic traces detected
- **Missing Outputs > 5**: Output loss pattern detected

#### **Medium Priority Alerts**

- **Completeness Score 90-94%**: System degraded but functional
- **Critical Issues 5-10**: Some issues detected
- **Orphaned Traces > 3**: Potential process termination issues

#### **Low Priority Alerts**

- **Completeness Score 95-99%**: Minor issues detected
- **Critical Issues 1-4**: Isolated problems

---

## 🚀 Integration Examples

### **Health Check Integration with Monitoring Systems**

#### **Prometheus Integration**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "agent-spy-health"
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: "/health/traces"
    scrape_interval: 30s
```

#### **Kubernetes Health Checks**

```yaml
# deployment.yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 📈 Success Metrics & KPIs

### **System Health KPIs**

1. **Uptime**: 99.9%+ system availability
2. **Response Time**: <100ms for health check endpoints
3. **Completeness Score**: >95% trace completeness
4. **Issue Detection**: <5 minutes from issue occurrence to detection

### **Trace Quality KPIs**

1. **Output Completeness**: 99.5%+ traces have outputs
2. **Status Consistency**: 99.9%+ traces have consistent status
3. **Hierarchy Integrity**: 99.8%+ trace hierarchies are complete

---

## 🚨 Troubleshooting

### **Common Issues & Solutions**

#### **Health Check Endpoint Unavailable**

**Symptoms**: 404 or 500 errors on health endpoints

**Solutions**:

1. Check if health endpoints are registered in FastAPI router
2. Verify database connectivity
3. Check application logs for errors

### **Debug Commands**

```bash
# Test health endpoints manually
curl -v http://localhost:8000/health
curl -v http://localhost:8000/health/ready
curl -v http://localhost:8000/health/live
curl -v http://localhost:8000/health/traces
```

---

## 📚 References

- **Implementation Files**:
  - `src/api/health.py` - Health check endpoints
  - `src/repositories/runs.py` - Trace completeness methods
  - `docs/plans/TRACE_OUTPUT_MISSING_ANALYSIS.md` - Implementation plan

---

**Document Version**: 1.0
**Last Updated**: September 2, 2025
**Implementation Phase**: Phase 4 Complete ✅
**Status**: Production Ready 🚀
