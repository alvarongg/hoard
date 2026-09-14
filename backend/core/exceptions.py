"""Domain exceptions for H.O.A.R.D. business logic.

These exceptions are raised by services and mapped to HTTP responses
by the exception handlers registered in main.py.
"""


class DomainError(Exception):
    """Base for all domain errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""

    pass


class DuplicateError(DomainError):
    """Raised when a resource already exists (e.g. duplicate name)."""

    pass


class ValidationError(DomainError):
    """Raised when a business validation rule is violated."""

    pass


class FileValidationError(DomainError):
    """Raised when an uploaded file fails validation (type, size, etc.)."""

    pass


class ToolUnavailableError(DomainError):
    """Raised when a required external tool (e.g. pg_dump) is missing."""

    pass
