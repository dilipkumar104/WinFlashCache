"""
Store module — Implements the in-memory database storage engine.

This module provides the `DataStore` class, which encapsulates a Python
dictionary to store and manage key-value pairs in memory. By wrapping the
dictionary, we can control how keys and values are set, checked, and deleted,
and prepare the database for serialization (saving/loading) in the future.

Day 4 update: All mutating methods now run validation before touching data.
Day 6 update: DataStore gains file persistence (write-through to JSON).
Day 7 update: DataStore gains TTL (Time-To-Live) expiry support.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional

from winflashcache.exceptions import KeyNotFoundError
from winflashcache.validators import validate_key, validate_value
from winflashcache.ttl import make_expiry, is_expired, remaining_ttl


class DataStore:
    """
    An in-memory key-value data store with write-through file persistence
    and TTL (Time-To-Live) key expiry.

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
        self._ttl: Dict[str, float] = {}   # key → expiry UNIX timestamp
        self.filepath = filepath
        if self.filepath:
            self.load()

    # ── Internal TTL helpers ────────────────────────────────────────────────

    def _purge_expired(self, key: str) -> bool:
        """
        Check if a single key has expired and remove it if so.

        Returns:
            True if the key was expired and purged, False otherwise.
        """
        if key in self._ttl and is_expired(self._ttl[key]):
            del self._data[key]
            del self._ttl[key]
            self.save()
            return True
        return False

    # ── Persistence Operations ───────────────────────────────────────────────

    def load(self, filepath: Optional[Path] = None) -> None:
        """
        Load data (and TTL metadata) from disk into the store.

        Args:
            filepath: Optional path to load from. Defaults to the configured filepath.
        """
        path = filepath or self.filepath
        if not path:
            return
        from winflashcache.persistence import load_from_disk
        self._data, self._ttl = load_from_disk(path)

    def save(self, filepath: Optional[Path] = None) -> None:
        """
        Save the current store data (and TTL metadata) to disk.

        Args:
            filepath: Optional path to save to. Defaults to the configured filepath.
        """
        path = filepath or self.filepath
        if not path:
            return
        from winflashcache.persistence import save_to_disk
        save_to_disk(self._data, path, ttl_data=self._ttl)

    # ── Write Operations ───────────────────────────────────────────────────

    def set(self, key: str, value: str, ttl: Optional[float] = None) -> None:
        """
        Store a value associated with a key, with an optional TTL.
        If the key already exists, its value (and TTL) is overwritten.

        Args:
            key:   The unique string identifier. Must pass key validation.
            value: The string value to store. Must pass value validation.
            ttl:   Optional number of seconds before this key expires.

        Raises:
            KeyValidationError:   If the key fails validation rules.
            ValueValidationError: If the value fails validation rules.
            ValueError:           If ttl is provided but is not positive.
        """
        validate_key(key)
        validate_value(value)
        self._data[key] = value

        if ttl is not None:
            self._ttl[key] = make_expiry(ttl)
        else:
            # Remove any existing TTL if key is overwritten without one
            self._ttl.pop(key, None)

        self.save()

    def delete(self, key: str) -> bool:
        """
        Remove a key and its value (and TTL) from the store.

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
            self._ttl.pop(key, None)
            self.save()
            return True
        return False

    def clear(self) -> None:
        """Remove all key-value pairs (and their TTLs) from the store."""
        self._data.clear()
        self._ttl.clear()
        self.save()

    # ── TTL Operations ─────────────────────────────────────────────────────

    def get_ttl(self, key: str) -> Optional[float]:
        """
        Return the number of seconds remaining before a key expires.

        Args:
            key: The key to inspect.

        Returns:
            Remaining seconds as a float, or None if the key has no TTL.

        Raises:
            KeyValidationError: If the key fails validation rules.
            KeyNotFoundError:   If the key is not in the store.
        """
        validate_key(key)
        # Check expiry first
        self._purge_expired(key)
        if key not in self._data:
            raise KeyNotFoundError(key)

        if key not in self._ttl:
            return None   # Key exists but has no expiry

        return remaining_ttl(self._ttl[key])

    # ── Read Operations ────────────────────────────────────────────────────

    def get(self, key: str) -> str:
        """
        Retrieve the value associated with a key.

        If the key has an expired TTL, it is purged transparently and
        a KeyNotFoundError is raised as if it never existed.

        Args:
            key: The key to look up. Must pass key validation.

        Returns:
            The stored string value.

        Raises:
            KeyValidationError: If the key fails validation rules.
            KeyNotFoundError:   If the key is not in the store or has expired.
        """
        validate_key(key)
        self._purge_expired(key)
        if key not in self._data:
            raise KeyNotFoundError(key)
        return self._data[key]

    def exists(self, key: str) -> bool:
        """
        Check if a key is present in the store (and not expired).

        Args:
            key: The key to check. Must pass key validation.

        Returns:
            True if the key exists and is not expired, False otherwise.

        Raises:
            KeyValidationError: If the key fails validation rules.
        """
        validate_key(key)
        self._purge_expired(key)
        return key in self._data

    def keys(self) -> List[str]:
        """
        Retrieve a sorted list of all stored keys, excluding expired ones.

        Returns:
            A sorted list of all live key strings currently in the store.
        """
        # Collect any expired keys and purge them in bulk
        expired = [k for k in list(self._data.keys()) if self._purge_expired(k)]
        return sorted(self._data.keys())

    def count(self) -> int:
        """
        Return the total number of live (non-expired) key-value pairs.

        Returns:
            The integer count of stored live keys.
        """
        # Purge expired keys before counting
        for k in list(self._data.keys()):
            self._purge_expired(k)
        return len(self._data)
