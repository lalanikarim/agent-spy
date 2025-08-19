# OTLP WebSocket Integration

## Overview

Agent Spy now supports real-time WebSocket updates for OTLP traces. This enables immediate dashboard updates when traces are received via OpenTelemetry Protocol.

## Implementation

### WebSocket Events

OTLP traces trigger the following WebSocket events:

- **`trace.created`**: Sent when a new trace is created from OTLP span
- **`trace.completed`**: Sent when a trace is completed (has end_time)

### Event Data Structure

```json
{
  "type": "trace.created",
  "data": {
    "trace_id": "uuid-string",
    "name": "span-name",
    "run_type": "chain|llm|tool|internal",
    "project_name": "service-name",
    "source": "otlp_http|otlp_grpc"
  }
}
```

### Integration Points

#### HTTP OTLP Receiver (`src/otel/receiver/http_server.py`)

- Broadcasts events after successful trace creation
- Source: `"otlp_http"`
- Handles protobuf and JSON formats

#### gRPC OTLP Receiver (`src/otel/receiver/grpc_server.py`)

- Broadcasts events after successful trace creation
- Source: `"otlp_grpc"`
- Handles standard OTLP gRPC protocol

### Error Handling

- WebSocket failures don't break OTLP processing
- UUID serialization handled properly
- Graceful degradation if WebSocket is unavailable

## Usage

### Real-time Updates

For immediate WebSocket updates, use `SimpleSpanProcessor`:

```python
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

processor = SimpleSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
```

### Batch Processing

For batch processing (less real-time), use `BatchSpanProcessor`:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
```

## Testing

### Real-time Updates

For immediate WebSocket updates, use `SimpleSpanProcessor`:

```python
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

processor = SimpleSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
```

### Batch Processing

For batch processing (less real-time), use `BatchSpanProcessor`:

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
```

### Example Integration

See `examples/test_langgraph_agent.py` for a complete example of OTLP integration with Agent Spy.

## Dashboard Integration

The frontend automatically receives WebSocket events and updates:

- Trace table in real-time
- Real-time notifications
- Connection status indicators
- Automatic cache invalidation

## Configuration

No additional configuration required. WebSocket integration is enabled by default when OTLP receivers are active.
