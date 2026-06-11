"""
validators.py — Input validation functions for keys and values.

Validation is the "bouncer at the door" — it inspects input before it
ever reaches the storage engine. If input is bad, a descriptive
exception is raised immediately, before any data is touched.

Rules enforced:
    KEY:
        - Cannot be empty or whitespace-only.
        - Maximum 128 characters.
        - Only letters (a-z, A-Z), digits (0-9), underscores (_),
          hyphens (-), and dots (.) are allowed.
          (Same character set used by Redis, environment variables, etc.)

    VALUE:
        - Cannot be empty.
        - Maximum 512 characters.
"""

import re

from winflashcache.exceptions import KeyValidationError, ValueValidationError


# ── Constants ─────────────────────────────────────────────────────────────────

# Maximum number of characters allowed in a key.
KEY_MAX_LENGTH: int = 128

# Maximum number of characters allowed in a value.
VALUE_MAX_LENGTH: int = 512

# A compiled regex that matches VALID key characters.
# ^ and $ anchor the pattern to the full string.
# + means "one or more of these characters".
_VALID_KEY_PATTERN: re.Pattern = re.compile(r"^[a-zA-Z0-9_.:-]+$")


# ── Public Validator Functions ─────────────────────────────────────────────────

def validate_key(key: str) -> None:
    """
    Validate a key string against our rules.

    This function returns None on success and raises KeyValidationError
    if the key fails any rule.

    Args:
        key: The key string to validate.

    Raises:
        KeyValidationError: If the key is empty, too long, or contains
                            invalid characters.

    Examples:
        >>> validate_key("user_name")    # OK — returns None
        >>> validate_key("")             # Raises KeyValidationError
        >>> validate_key("my key!")      # Raises KeyValidationError
        >>> validate_key("a" * 200)      # Raises KeyValidationError
    """
    # Rule 1: Must not be empty or whitespace-only.
    if not key or not key.strip():
        raise KeyValidationError(key, "key cannot be empty or whitespace.")

    # Rule 2: Must not exceed the maximum length.
    if len(key) > KEY_MAX_LENGTH:
        raise KeyValidationError(
            key,
            f"key is too long ({len(key)} chars). Maximum allowed is {KEY_MAX_LENGTH}.",
        )

    # Rule 3: Must only contain allowed characters.
    if not _VALID_KEY_PATTERN.match(key):
        raise KeyValidationError(
            key,
            "only letters, digits, '_', '-', ':', and '.' are allowed in keys.",
        )


def validate_value(value: str) -> None:
    """
    Validate a value string against our rules.

    This function returns None on success and raises ValueValidationError
    if the value fails any rule.

    Args:
        value: The value string to validate.

    Raises:
        ValueValidationError: If the value is empty or too long.

    Examples:
        >>> validate_value("hello")           # OK — returns None
        >>> validate_value("")                # Raises ValueValidationError
        >>> validate_value("x" * 600)        # Raises ValueValidationError
    """
    # Rule 1: Must not be empty.
    if not value:
        raise ValueValidationError(value, "value cannot be empty.")

    # Rule 2: Must not exceed the maximum length.
    if len(value) > VALUE_MAX_LENGTH:
        raise ValueValidationError(
            value,
            f"value is too long ({len(value)} chars). Maximum allowed is {VALUE_MAX_LENGTH}.",
        )
