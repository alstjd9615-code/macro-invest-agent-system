"""Unit tests for core/exceptions/base.py."""

import pytest

from core.exceptions.base import (
    AppError,
    ConflictError,
    ConfigurationError,
    DomainError,
    InternalError,
    MCPToolError,
    NotFoundError,
    StorageError,
    ValidationError,
)


class TestAppError:
    """AppError carries the expected attributes and defaults."""

    def test_message_stored(self) -> None:
        exc = AppError("something went wrong")
        assert exc.message == "something went wrong"
        assert str(exc) == "something went wrong"

    def test_default_error_code(self) -> None:
        exc = AppError("msg")
        assert exc.error_code == "APP_ERROR"

    def test_custom_error_code(self) -> None:
        exc = AppError("msg", error_code="CUSTOM_CODE")
        assert exc.error_code == "CUSTOM_CODE"

    def test_default_detail_is_empty_dict(self) -> None:
        exc = AppError("msg")
        assert exc.detail == {}

    def test_custom_detail(self) -> None:
        exc = AppError("msg", detail={"key": "value"})
        assert exc.detail == {"key": "value"}

    def test_is_exception(self) -> None:
        exc = AppError("msg")
        assert isinstance(exc, Exception)


class TestSubclassErrorCodes:
    """Each subclass has the expected default error_code."""

    @pytest.mark.parametrize(
        ("cls", "expected_code"),
        [
            (ValidationError, "VALIDATION_ERROR"),
            (NotFoundError, "NOT_FOUND"),
            (ConflictError, "CONFLICT"),
            (InternalError, "INTERNAL_ERROR"),
            (StorageError, "STORAGE_ERROR"),
            (ConfigurationError, "CONFIGURATION_ERROR"),
            (DomainError, "DOMAIN_ERROR"),
            (MCPToolError, "MCP_TOOL_ERROR"),
        ],
    )
    def test_default_error_code(self, cls: type[AppError], expected_code: str) -> None:
        exc = cls("test message")
        assert exc.error_code == expected_code


class TestSubclassInheritance:
    """All subclasses inherit from AppError."""

    def test_validation_error_is_app_error(self) -> None:
        assert issubclass(ValidationError, AppError)

    def test_not_found_is_app_error(self) -> None:
        assert issubclass(NotFoundError, AppError)

    def test_domain_error_is_app_error(self) -> None:
        assert issubclass(DomainError, AppError)

    def test_mcp_tool_error_is_app_error(self) -> None:
        assert issubclass(MCPToolError, AppError)


class TestRaiseAndCatch:
    """Exceptions can be raised and caught as expected."""

    def test_raise_and_catch_as_app_error(self) -> None:
        with pytest.raises(AppError) as exc_info:
            raise NotFoundError("Signal not found.", detail={"id": "abc"})
        assert exc_info.value.error_code == "NOT_FOUND"
        assert exc_info.value.detail["id"] == "abc"

    def test_raise_and_catch_as_specific_type(self) -> None:
        with pytest.raises(NotFoundError):
            raise NotFoundError("Missing resource.")

    def test_error_code_override_on_subclass(self) -> None:
        exc = ValidationError("bad input", error_code="CUSTOM_VALIDATION")
        assert exc.error_code == "CUSTOM_VALIDATION"
