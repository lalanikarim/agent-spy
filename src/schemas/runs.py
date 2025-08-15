"""Pydantic models for run/trace data compatible with LangSmith."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RunTypeEnum(str):
    """Run type enumeration matching LangSmith."""
    
    LLM = "llm"
    CHAIN = "chain"
    TOOL = "tool"
    RETRIEVER = "retriever"
    EMBEDDING = "embedding"
    PROMPT = "prompt"
    PARSER = "parser"


class RunBase(BaseModel):
    """Base model for runs matching LangSmith RunBase schema."""
    
    # Required fields
    name: str = Field(..., description="Name of the run")
    start_time: datetime = Field(..., description="Start time of the run")
    run_type: str = Field(..., description="Type of run (llm, chain, tool, etc.)")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input data")
    
    # Optional core fields
    id: Optional[UUID] = Field(default_factory=uuid4, description="Unique run ID")
    end_time: Optional[datetime] = Field(None, description="End time of the run")
    outputs: Optional[dict[str, Any]] = Field(None, description="Output data")
    error: Optional[str] = Field(None, description="Error message if run failed")
    
    # Hierarchy fields
    parent_run_id: Optional[UUID] = Field(None, description="Parent run ID")
    trace_id: Optional[UUID] = Field(None, description="Trace ID for grouping related runs")
    session_id: Optional[UUID] = Field(None, description="Session ID")
    session_name: Optional[str] = Field(None, description="Session name")
    
    # Metadata fields
    extra: Optional[dict[str, Any]] = Field(None, description="Extra metadata")
    serialized: Optional[dict[str, Any]] = Field(None, description="Serialized component info")
    events: Optional[list[dict[str, Any]]] = Field(None, description="Events during run")
    tags: Optional[list[str]] = Field(None, description="Tags for categorization")
    
    # Reference fields
    reference_example_id: Optional[UUID] = Field(None, description="Reference example ID")
    manifest_id: Optional[UUID] = Field(None, description="Manifest ID")
    
    # Attachment fields (simplified for now)
    input_attachments: Optional[dict[str, Any]] = Field(None, description="Input attachments")
    output_attachments: Optional[dict[str, Any]] = Field(None, description="Output attachments")
    attachments: Optional[dict[str, Any]] = Field(None, description="General attachments")
    
    # S3 URL fields (for large data)
    inputs_s3_urls: Optional[dict[str, str]] = Field(None, description="S3 URLs for large inputs")
    outputs_s3_urls: Optional[dict[str, str]] = Field(None, description="S3 URLs for large outputs")
    
    # Ordering field
    dotted_order: Optional[str] = Field(None, description="Dotted order for hierarchical sorting")


class RunCreate(RunBase):
    """Model for creating new runs."""
    
    # Override ID to be required for creation (LangSmith compatibility)
    id: UUID = Field(..., description="Run ID (required for LangSmith compatibility)")
    
    # Add project_name field
    project_name: Optional[str] = Field(None, description="Project name")


class RunUpdate(BaseModel):
    """Model for updating existing runs."""
    
    # ID is required to identify which run to update
    id: UUID = Field(..., description="ID of the run to update")
    
    # All other fields optional for updates
    name: Optional[str] = None
    end_time: Optional[datetime] = None
    outputs: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    extra: Optional[dict[str, Any]] = None
    events: Optional[list[dict[str, Any]]] = None
    tags: Optional[list[str]] = None
    parent_run_id: Optional[UUID] = None
    reference_example_id: Optional[UUID] = None
    
    # Token usage fields (for LLM runs)
    prompt_tokens: Optional[int] = Field(None, description="Number of prompt tokens")
    completion_tokens: Optional[int] = Field(None, description="Number of completion tokens")
    total_tokens: Optional[int] = Field(None, description="Total number of tokens")
    
    # Cost fields
    total_cost: Optional[Decimal] = Field(None, description="Total cost")
    prompt_cost: Optional[Decimal] = Field(None, description="Prompt cost")
    completion_cost: Optional[Decimal] = Field(None, description="Completion cost")
    
    # Timing fields
    first_token_time: Optional[datetime] = Field(None, description="Time of first token")


class RunResponse(RunBase):
    """Model for run responses with additional computed fields."""
    
    # Always present in responses
    id: UUID = Field(..., description="Run ID")
    
    # Child runs (for hierarchical display)
    child_run_ids: Optional[list[UUID]] = Field(None, description="Child run IDs")
    child_runs: Optional[list["RunResponse"]] = Field(None, description="Child runs")
    
    # Statistics and metadata
    feedback_stats: Optional[dict[str, Any]] = Field(None, description="Feedback statistics")
    status: Optional[str] = Field(None, description="Run status")
    app_path: Optional[str] = Field(None, description="Application path")
    
    # Token usage (computed from events or stored)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Cost information
    total_cost: Optional[Decimal] = None
    prompt_cost: Optional[Decimal] = None
    completion_cost: Optional[Decimal] = None
    
    # Additional computed fields
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    in_dataset: Optional[bool] = Field(None, description="Whether run is in a dataset")
    
    @classmethod
    def from_run(cls, run: Any) -> "RunResponse":
        """Create a RunResponse from a database Run model."""
        # Calculate duration if both start and end times are available
        duration_ms = None
        if run.start_time and run.end_time:
            duration = run.end_time - run.start_time
            duration_ms = int(duration.total_seconds() * 1000)
        
        return cls(
            id=run.id,
            name=run.name,
            start_time=run.start_time,
            end_time=run.end_time,
            run_type=run.run_type,
            inputs=run.inputs or {},
            outputs=run.outputs,
            error=run.error,
            parent_run_id=run.parent_run_id,
            extra=run.extra,
            serialized=run.serialized,
            events=run.events,
            tags=run.tags,
            reference_example_id=run.reference_example_id,
            status=run.status,
            duration_ms=duration_ms,
        )


class BatchIngestRequest(BaseModel):
    """Model for batch ingestion requests."""
    
    post: list[RunCreate] = Field(default_factory=list, description="Runs to create")
    patch: list[RunUpdate] = Field(default_factory=list, description="Runs to update")
    pre_sampled: bool = Field(False, description="Whether data is pre-sampled")


class BatchIngestResponse(BaseModel):
    """Response for batch ingestion."""
    
    success: bool = Field(..., description="Whether ingestion was successful")
    created_count: int = Field(0, description="Number of runs created")
    updated_count: int = Field(0, description="Number of runs updated")
    errors: list[str] = Field(default_factory=list, description="Any errors encountered")


class LangSmithInfo(BaseModel):
    """LangSmith service information response."""
    
    version: str = Field(..., description="Service version")
    license_expiration_time: Optional[datetime] = Field(None, description="License expiration")
    batch_ingest_config: dict[str, Any] = Field(
        default_factory=lambda: {
            "size_limit": 20_971_520,  # 20MB
            "size_limit_bytes": 20_971_520,
            "scale_up_qsize_trigger": 1000,
            "scale_up_nthreads_limit": 16,
            "scale_down_nempty_trigger": 4,
        },
        description="Batch ingestion configuration"
    )
    tenant_handle: Optional[str] = Field(None, description="Tenant handle")


# Enable forward references for recursive models
RunResponse.model_rebuild()
