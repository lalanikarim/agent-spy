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
