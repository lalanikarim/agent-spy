"""OTLP Forwarder Configuration."""

from pydantic import BaseModel


class OtlpForwarderConfig(BaseModel):
    """Configuration for OTLP forwarder"""

    enabled: bool = False
    endpoint: str = ""
    protocol: str = "grpc"  # "http" or "grpc"
    service_name: str = "agent-spy-forwarder"
    timeout: int = 30
    retry_count: int = 3
    headers: dict[str, str] | None = None
    insecure: bool = True
    debounce_seconds: float = 5.0
    forward_run_timeout_seconds: float = 30.0
    max_synthetic_spans: int = 10
    attr_max_str: int = 500
    attr_max_kv_str: int = 200
    attr_max_list_items: int = 5
