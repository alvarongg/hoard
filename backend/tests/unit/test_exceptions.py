"""Unit tests for domain exception classes."""

import pytest

from core.exceptions import (
    DomainError,
    DuplicateError,
    FileValidationError,
    NotFoundError,
    ValidationError,
)


class TestDomainError:
    def test_stores_message(self) -> None:
        exc = DomainError("something went wrong")
        assert exc.message == "something went wrong"

    def test_str_representation(self) -> None:
        exc = DomainError("oops")
        assert str(exc) == "oops"

    def test_is_base_exception(self) -> None:
        exc = DomainError("base")
        assert isinstance(exc, Exception)


class TestNotFoundError:
    def test_stores_message(self) -> None:
        exc = NotFoundError("Collection not found")
        assert exc.message == "Collection not found"

    def test_is_domain_error(self) -> None:
        exc = NotFoundError("missing")
        assert isinstance(exc, DomainError)


class TestDuplicateError:
    def test_stores_message(self) -> None:
        exc = DuplicateError("Name already exists")
        assert exc.message == "Name already exists"

    def test_is_domain_error(self) -> None:
        exc = DuplicateError("dup")
        assert isinstance(exc, DomainError)


class TestValidationError:
    def test_stores_message(self) -> None:
        exc = ValidationError("Invalid category")
        assert exc.message == "Invalid category"

    def test_is_domain_error(self) -> None:
        exc = ValidationError("bad")
        assert isinstance(exc, DomainError)


class TestFileValidationError:
    def test_stores_message(self) -> None:
        exc = FileValidationError("File too large")
        assert exc.message == "File too large"

    def test_is_domain_error(self) -> None:
        exc = FileValidationError("bad file")
        assert isinstance(exc, DomainError)


class TestExceptionHierarchy:
    """Verify all domain exceptions are catchable via DomainError."""

    @pytest.mark.parametrize(
        "exc_class",
        [NotFoundError, DuplicateError, ValidationError, FileValidationError],
    )
    def test_subclass_caught_by_domain_error(
        self, exc_class: type[DomainError]
    ) -> None:
        with pytest.raises(DomainError):
            raise exc_class("test")
