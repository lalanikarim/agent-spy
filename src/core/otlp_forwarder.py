"""Global OTLP forwarder instance management."""


from src.core.logging import get_logger

logger = get_logger(__name__)

# Global OTLP forwarder instance
_otlp_forwarder = None


def set_otlp_forwarder(forwarder) -> None:
    """Set the global OTLP forwarder instance."""
    global _otlp_forwarder
    _otlp_forwarder = forwarder
    if forwarder:
        logger.info("Global OTLP forwarder instance set")
    else:
        logger.info("Global OTLP forwarder instance cleared")


def get_otlp_forwarder():
    """Get the global OTLP forwarder instance."""
    return _otlp_forwarder
