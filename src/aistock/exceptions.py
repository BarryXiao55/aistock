"""Aistock exception hierarchy."""


class PipelineError(Exception):
    """Pipeline base exception."""


class SourceError(PipelineError):
    """Data source layer exception."""


class SourceUnavailable(SourceError):
    """Data source unreachable."""


class SourceRateLimited(SourceError):
    """Data source rate-limited."""


class CleanError(PipelineError):
    """Cleaning layer exception."""


class ValidationError(CleanError):
    """Schema validation failed."""


class StoreError(PipelineError):
    """Storage layer exception."""


class WriteError(StoreError):
    """Write operation failed."""


class BackendUnavailable(StoreError):
    """Storage backend unreachable."""
