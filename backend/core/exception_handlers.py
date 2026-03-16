"""Global exception handlers that map domain exceptions to HTTP responses."""

from fastapi import Request
from fastapi.responses import JSONResponse

from core.exceptions import (
    DuplicateError,
    FileValidationError,
    NotFoundError,
    ValidationError,
)


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Map NotFoundError to 404."""
    return JSONResponse(status_code=404, content={"detail": exc.message})


async def duplicate_handler(request: Request, exc: DuplicateError) -> JSONResponse:
    """Map DuplicateError to 409."""
    return JSONResponse(status_code=409, content={"detail": exc.message})


async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Map ValidationError to 422."""
    return JSONResponse(status_code=422, content={"detail": exc.message})


async def file_validation_handler(
    request: Request, exc: FileValidationError
) -> JSONResponse:
    """Map FileValidationError to 422."""
    return JSONResponse(status_code=422, content={"detail": exc.message})
