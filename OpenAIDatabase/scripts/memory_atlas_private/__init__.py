"""Memory Atlas private, lossless data spine.

The package separates immutable object bytes, durable structured facts, and
rebuildable runtime state. It intentionally performs no model calls.
"""

from .config import RuntimeConfig, ConfigurationError
from .failure_compound import FailureCompoundStore
from .pipeline import CapturePipeline, RemoteReconcilePipeline

__all__ = [
    "RuntimeConfig",
    "ConfigurationError",
    "FailureCompoundStore",
    "CapturePipeline",
    "RemoteReconcilePipeline",
]
