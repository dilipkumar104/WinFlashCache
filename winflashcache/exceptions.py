"""
exceptions.py — Custom exception types for WinFlashCache.

Instead of using bare Python exceptions like ValueError or KeyError,
we define our own hierarchy. This has two big benefits:

1. PRECISION — We can write `except KeyNotFoundError` and know we are
   catching *only* our own "key not found" errors, not some unrelated
   KeyError deep inside a library.

2. CONTEXT — Each exception can carry extra information (like the bad
   key name) so the error message is specific and helpful.

Hierarchy:
    WinFlashCacheError          (base for all our exceptions)
    ├── KeyNotFoundError        (get/del on a missing key)
    ├── KeyValidationError      (key fails format rules)
    └── ValueValidationError    (value fails format rules)
"""


class WinFlashCacheError(Exception):
    """
    Base class for all WinFlashCache exceptions.

    Catching this type catches any error our application raises,
    which is useful in the CLI's top-level error handler.
    """

    # A short, human-readable label shown in the error prefix.
    # Subclasses override this to get a specific prefix.
    label: str = "ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"[{self.label}] {self.message}"


class KeyNotFoundError(WinFlashCacheError):
    """
    Raised when a key is looked up but does not exist in the store.

    Example:
        >>> store.get("ghost_key")
        KeyNotFoundError: [KEY_NOT_FOUND] No key named 'ghost_key' in the store.

    Attributes:
        key: The key that was not found.
    """

    label = "KEY_NOT_FOUND"

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"No key named '{key}' in the store.")


class KeyValidationError(WinFlashCacheError):
    """
    Raised when a key string fails our validation rules.

    Validation rules (see validators.py for full details):
        - Must not be empty.
        - Must be <= 128 characters long.
        - Must contain only letters, digits, underscores, hyphens, or dots.

    Example:
        >>> validate_key("my key!")
        KeyValidationError: [KEY_INVALID] Key 'my key!' contains invalid
        characters. Only letters, digits, '_', '-', and '.' are allowed.

    Attributes:
        key: The invalid key string.
    """

    label = "KEY_INVALID"

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        super().__init__(f"Key '{key}' is invalid — {reason}")


class ValueValidationError(WinFlashCacheError):
    """
    Raised when a value string fails our validation rules.

    Validation rules (see validators.py for full details):
        - Must not be empty.
        - Must be <= 512 characters long.

    Attributes:
        value: The invalid value string.
    """

    label = "VALUE_INVALID"

    def __init__(self, value: str, reason: str) -> None:
        self.value = value
        super().__init__(f"Value is invalid — {reason}")
