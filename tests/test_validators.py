"""
test_validators.py — Unit tests for the key and value validation rules.

These tests verify that our "bouncer" functions accept valid input
and reject invalid input with the right exception types.

Run these tests:
    python -m pytest tests/test_validators.py -v
"""

import pytest

from winflashcache.validators import validate_key, validate_value, KEY_MAX_LENGTH, VALUE_MAX_LENGTH
from winflashcache.exceptions import KeyValidationError, ValueValidationError


# =============================================================================
# KEY VALIDATION TESTS
# =============================================================================

class TestValidateKey:
    """Tests for the validate_key() function."""

    # ── Valid keys (should NOT raise) ──────────────────────────────────────

    def test_simple_lowercase_key(self):
        """A plain lowercase word is a valid key."""
        validate_key("username")   # Must not raise

    def test_mixed_case_key(self):
        """Keys are case-sensitive and mixed-case is valid."""
        validate_key("UserName")

    def test_key_with_underscore(self):
        """Underscores are allowed in keys."""
        validate_key("user_name")

    def test_key_with_hyphen(self):
        """Hyphens are allowed in keys."""
        validate_key("user-name")

    def test_key_with_dot(self):
        """Dots are allowed in keys (useful for namespacing like 'app.config')."""
        validate_key("app.config")

    def test_key_with_colon(self):
        """Colons are allowed in keys (Redis-style namespacing like 'user:42')."""
        validate_key("user:42")

    def test_key_with_digits(self):
        """Keys containing only digits are valid."""
        validate_key("12345")

    def test_key_at_max_length(self):
        """A key exactly at the maximum allowed length is valid."""
        validate_key("a" * KEY_MAX_LENGTH)

    # ── Invalid keys (SHOULD raise KeyValidationError) ─────────────────────

    def test_empty_key_raises(self):
        """An empty string is not a valid key."""
        with pytest.raises(KeyValidationError):
            validate_key("")

    def test_whitespace_only_key_raises(self):
        """A whitespace-only string is not a valid key."""
        with pytest.raises(KeyValidationError):
            validate_key("   ")

    def test_key_with_space_raises(self):
        """Spaces are not allowed in keys."""
        with pytest.raises(KeyValidationError):
            validate_key("my key")

    def test_key_with_exclamation_raises(self):
        """Special characters like '!' are not allowed."""
        with pytest.raises(KeyValidationError):
            validate_key("key!")

    def test_key_with_at_symbol_raises(self):
        """The '@' symbol is not allowed in keys."""
        with pytest.raises(KeyValidationError):
            validate_key("user@host")

    def test_key_exceeding_max_length_raises(self):
        """A key one character over the limit is rejected."""
        with pytest.raises(KeyValidationError):
            validate_key("a" * (KEY_MAX_LENGTH + 1))

    def test_error_message_contains_key_name(self):
        """The exception message should mention the offending key."""
        bad_key = "bad key!"
        with pytest.raises(KeyValidationError) as exc_info:
            validate_key(bad_key)
        assert bad_key in str(exc_info.value)


# =============================================================================
# VALUE VALIDATION TESTS
# =============================================================================

class TestValidateValue:
    """Tests for the validate_value() function."""

    # ── Valid values (should NOT raise) ────────────────────────────────────

    def test_simple_string_value(self):
        """A plain string is a valid value."""
        validate_value("hello world")

    def test_value_with_special_characters(self):
        """Values can contain any characters including spaces and symbols."""
        validate_value("Hello, World! @#$%^&*()")

    def test_numeric_string_value(self):
        """Numeric strings are valid values."""
        validate_value("42")

    def test_value_at_max_length(self):
        """A value exactly at the maximum length is valid."""
        validate_value("v" * VALUE_MAX_LENGTH)

    # ── Invalid values (SHOULD raise ValueValidationError) ─────────────────

    def test_empty_value_raises(self):
        """An empty string is not a valid value."""
        with pytest.raises(ValueValidationError):
            validate_value("")

    def test_value_exceeding_max_length_raises(self):
        """A value one character over the limit is rejected."""
        with pytest.raises(ValueValidationError):
            validate_value("v" * (VALUE_MAX_LENGTH + 1))

    def test_error_message_contains_reason(self):
        """The exception message should explain why the value is invalid."""
        with pytest.raises(ValueValidationError) as exc_info:
            validate_value("")
        # Should mention the word "empty" in the message
        assert "empty" in str(exc_info.value)
