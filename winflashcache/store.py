"""
Store module — Implements the in-memory database storage engine.

This module provides the `DataStore` class, which encapsulates a Python
dictionary to store and manage key-value pairs in memory. By wrapping the
dictionary, we can control how keys and values are set, checked, and deleted,
and prepare the database for serialization (saving/loading) in the future.

Day 4 update: All mutating methods now run validation before touching data.
"""

from pathlib import Path
from typing import Dict, List, Optional

from winflashcache.exceptions import KeyNotFoundError
from winflashcache.validators import validate_key, validate_value


class DataStore:
    """
    An in-memory key-value data store with write-through file persistence.

    This acts as a wrapper around a standard Python dictionary, providing
    isolated and validated operations corresponding to our CLI commands.

    All methods validate their inputs before performing any operation and
    raise descriptive custom exceptions on failure.
    """

    def __init__(self, filepath: Optional[Path] = None) -> None:
        """
        Initialize a key-value store.

        If a filepath is provided, the store loads existing data from it
        on initialization.
        """
        self._data: Dict[str, str] = {}
        self.filepath = filepath
        if self.filepath:
            self.load()

    # ── Persistence Operations ───────────────────────────────────────────────

    def load(self, filepath: Optional[Path] = None) -> None:
        """
        Load data from disk into the store.

        Args:
            filepath: Optional path to load from. Defaults to the configured filepath.
        """
        path = filepath or self.filepath
        if not path:
            return
        from winflashcache.persistence import load_from_disk
        self._data = load_from_disk(path)

    def save(self, filepath: Optional[Path] = None) -> None:
        """
        Save the current store data to disk.

        Args:
            filepath: Optional path to save to. Defaults to the configured filepath.
        """
        path = filepath or self.filepath
        if not path:
            return
        from winflashcache.persistence import save_to_disk
        save_to_disk(self._data, path)

    # ── Write Operations ───────────────────────────────────────────────────

    def set(self, key: str, value: str) -> None:
        """
        Store a value associated with a key.
        If the key already exists, its value is overwritten.

        Args:
            key:   The unique string identifier. Must pass key validation.
            value: The string value to store. Must pass value validation.

        Raises:
            KeyValidationError:   If the key fails validation rules.
            ValueValidationError: If the value fails validation rules.
        """
        validate_key(key)
        validate_value(value)
        self._data[key] = value
        self.save()

    def delete(self, key: str) -> bool:
        """
        Remove a key and its value from the store.

        Args:
            key: The key to delete. Must pass key validation.

        Returns:
            True if the key existed and was deleted, False otherwise.

        Raises:
            KeyValidationError: If the key fails validation rules.
        """
        validate_key(key)
        if key in self._data:
            del self._data[key]
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Remove all key-value pairs from the store."""
        self._data.clear()
        self.save()

    # ── Read Operations ────────────────────────────────────────────────────

    def get(self, key: str) -> str:
        """
        Retrieve the value associated with a key.

        Unlike before, this now raises KeyNotFoundError if the key is
        absent, rather than returning None. This forces the caller to
        handle the missing-key case explicitly.

        Args:
            key: The key to look up. Must pass key validation.

        Returns:
            The stored string value.

        Raises:
            KeyValidationError: If the key fails validation rules.
            KeyNotFoundError:   If the key is not in the store.
        """
        validate_key(key)
        if key not in self._data:
            raise KeyNotFoundError(key)
        return self._data[key]

    def exists(self, key: str) -> bool:
        """
        Check if a key is present in the store.

        Args:
            key: The key to check. Must pass key validation.

        Returns:
            True if the key exists, False otherwise.

        Raises:
            KeyValidationError: If the key fails validation rules.
        """
        validate_key(key)
        return key in self._data

    def keys(self) -> List[str]:
        """
        Retrieve a sorted list of all stored keys.

        Returns:
            A sorted list of all key strings currently in the store.
        """
        return sorted(self._data.keys())

    def count(self) -> int:
        """
        Return the total number of key-value pairs stored.

        Returns:
            The integer count of stored keys.
        """
        return len(self._data)
