"""
test_exceptions.py — Unit tests for custom exception classes.

These tests verify that our exceptions carry the right data and
produce well-formatted messages. They are small but important —
they guarantee that any code catching our exceptions can rely
on consistent attributes like `.key` and `.message`.

Run these tests:
    python -m pytest tests/test_exceptions.py -v
"""

import pytest

from winflashcache.exceptions import (
    WinFlashCacheError,
    KeyNotFoundError,
    KeyValidationError,
    ValueValidationError,
)


class TestExceptionHierarchy:
    """All custom exceptions must inherit from WinFlashCacheError."""

    def test_key_not_found_is_subclass(self):
        assert issubclass(KeyNotFoundError, WinFlashCacheError)

    def test_key_validation_error_is_subclass(self):
        assert issubclass(KeyValidationError, WinFlashCacheError)

    def test_value_validation_error_is_subclass(self):
        assert issubclass(ValueValidationError, WinFlashCacheError)

    def test_base_exception_is_subclass_of_exception(self):
        """WinFlashCacheError must ultimately be a Python Exception."""
        assert issubclass(WinFlashCacheError, Exception)


class TestKeyNotFoundError:
    """Tests for KeyNotFoundError attributes and formatting."""

    def test_stores_key_attribute(self):
        """The .key attribute holds the missing key name."""
        exc = KeyNotFoundError("ghost")
        assert exc.key == "ghost"

    def test_message_contains_key(self):
        """The string representation mentions the key name."""
        exc = KeyNotFoundError("my_key")
        assert "my_key" in str(exc)

    def test_label_is_key_not_found(self):
        """The label prefix is KEY_NOT_FOUND."""
        exc = KeyNotFoundError("x")
        assert exc.label == "KEY_NOT_FOUND"

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught as WinFlashCacheError."""
        with pytest.raises(WinFlashCacheError):
            raise KeyNotFoundError("test_key")


class TestKeyValidationError:
    """Tests for KeyValidationError attributes and formatting."""

    def test_stores_key_attribute(self):
        """The .key attribute holds the invalid key."""
        exc = KeyValidationError("bad key", "spaces not allowed")
        assert exc.key == "bad key"

    def test_message_contains_key_and_reason(self):
        """The error message includes both the key and the reason."""
        exc = KeyValidationError("bad key", "spaces not allowed")
        assert "bad key" in str(exc)
        assert "spaces not allowed" in str(exc)

    def test_label_is_key_invalid(self):
        """The label prefix is KEY_INVALID."""
        exc = KeyValidationError("x", "reason")
        assert exc.label == "KEY_INVALID"


class TestValueValidationError:
    """Tests for ValueValidationError attributes and formatting."""

    def test_stores_value_attribute(self):
        """The .value attribute holds the invalid value."""
        exc = ValueValidationError("", "cannot be empty")
        assert exc.value == ""

    def test_message_contains_reason(self):
        """The error message includes the reason."""
        exc = ValueValidationError("", "cannot be empty")
        assert "cannot be empty" in str(exc)

    def test_label_is_value_invalid(self):
        """The label prefix is VALUE_INVALID."""
        exc = ValueValidationError("x", "reason")
        assert exc.label == "VALUE_INVALID"
