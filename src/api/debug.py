"""Debug API endpoints for OpenTelemetry SDK compatibility analysis."""

import json
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.core.logging import get_logger

logger = get_logger(__name__)

# Global storage for debugging (in production, this would be a database)
debug_requests = []

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/otlp/")
async def debug_otlp_receiver(request: Request):
    """Debug endpoint that logs all incoming OTLP requests."""

    # Capture request metadata
    timestamp = datetime.now().isoformat()
    headers = dict(request.headers)
    content_type = headers.get("content-type", "unknown")

    # Capture request body
    body = await request.body()

    # Handle different content types
    if content_type == "application/x-protobuf":
        # Don't try to decode protobuf as UTF-8
        body_text = f"[Protobuf data - {len(body)} bytes]"
    else:
        # Try to decode as UTF-8 for JSON or other text formats
        try:
            body_text = body.decode("utf-8") if body else ""
        except UnicodeDecodeError:
            body_text = f"[Binary data - {len(body)} bytes]"

    # Try to parse as JSON or handle protobuf
    body_json = None
    try:
        if body_text:
            body_json = json.loads(body_text)
    except json.JSONDecodeError:
        # Check if it's protobuf data
        if body and len(body) > 0:
            # Convert protobuf bytes to hex for debugging
            hex_data = body.hex()[:200]  # First 200 hex chars
            body_json = {
                "error": "Not valid JSON - appears to be protobuf data",
                "content_type": content_type,
                "body_size": len(body),
                "hex_preview": hex_data,
                "raw_preview": body_text[:200] if body_text else "No text content",
            }
        else:
            body_json = {"error": "Not valid JSON", "raw": body_text[:500]}

    # Create debug record
    debug_record = {
        "timestamp": timestamp,
        "method": request.method,
        "url": str(request.url),
        "headers": headers,
        "content_type": content_type,
        "body_size": len(body),
        "body_text": body_text[:1000],  # Limit for readability
        "body_json": body_json,
        "query_params": dict(request.query_params),
    }

    # Store for analysis (in production, this would be stored in database)
    debug_requests.append(debug_record)

    # Print summary
    print(f"\n🔍 DEBUG: Received OTLP request at {timestamp}")
    print(f"   Content-Type: {content_type}")
    print(f"   Body Size: {len(body)} bytes")
    print(f"   Headers: {list(headers.keys())}")

    if body_json and isinstance(body_json, dict) and "resourceSpans" in body_json:
        spans_count = sum(
            len(scope_spans.get("spans", []))
            for resource_span in body_json.get("resourceSpans", [])
            for scope_spans in resource_span.get("scopeSpans", [])
        )
        print(f"   Spans Count: {spans_count}")

        # Show first span details
        for resource_span in body_json.get("resourceSpans", []):
            for scope_spans in resource_span.get("scopeSpans", []):
                for span in scope_spans.get("spans", [])[:1]:  # First span only
                    print(f"   First Span: {span.get('name', 'unknown')}")
                    print(f"   Trace ID: {span.get('traceId', 'unknown')}")
                    print(f"   Span ID: {span.get('spanId', 'unknown')}")
                    break
                break
            break

    # Return success response
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Debug endpoint received request",
            "timestamp": timestamp,
            "body_size": len(body),
            "spans_processed": 1,  # Mock response
        },
    )


@router.get("/requests/")
async def get_debug_requests():
    """Get all received debug requests."""
    return {
        "total_requests": len(debug_requests),
        "requests": debug_requests[-10:],  # Last 10 requests
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/clear/")
async def clear_debug_requests():
    """Clear all debug requests."""
    global debug_requests
    count = len(debug_requests)
    debug_requests = []
    return {"message": f"Cleared {count} debug requests", "timestamp": datetime.now().isoformat()}


@router.get("/health/")
async def debug_health_check():
    """Health check endpoint for debug service."""
    return {
        "status": "healthy",
        "service": "debug-otlp-receiver",
        "timestamp": datetime.now().isoformat(),
        "total_requests": len(debug_requests),
    }
