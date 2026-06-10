"""
Store module — Implements the in-memory database storage engine.

This module provides the `DataStore` class, which encapsulates a Python
dictionary to store and manage key-value pairs in memory. By wrapping the
dictionary, we can control how keys and values are set, checked, and deleted,
and prepare the database for serialization (saving/loading) in the future.
"""

from typing import Dict, List, Optional


class DataStore:
    """
    An in-memory key-value data store.
    
    This acts as a wrapper around a standard Python dictionary, providing
    isolated operations corresponding to our CLI commands.
    """
    
    def __init__(self) -> None:
        """Initialize an empty key-value store."""
        # Our primary in-memory hash map
        self._data: Dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        """
        Store a value associated with a key.
        If the key already exists, its value is overwritten.
        
        Args:
            key: The unique string identifier.
            value: The string value to store.
        """
        self._data[key] = value

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve the value associated with a key.
        
        Args:
            key: The key to look up.
            
        Returns:
            The stored string value if found, or None if the key does not exist.
        """
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        """
        Remove a key and its value from the store.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if the key existed and was deleted, False otherwise.
        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """
        Check if a key is present in the store.
        
        Args:
            key: The key to check.
            
        Returns:
            True if the key exists, False otherwise.
        """
        return key in self._data

    def keys(self) -> List[str]:
        """
        Retrieve a list of all stored keys.
        
        Returns:
            A list of all key strings.
        """
        return list(self._data.keys())

    def count(self) -> int:
        """
        Return the total number of key-value pairs stored.
        
        Returns:
            The integer count of stored keys.
        """
        return len(self._data)

    def clear(self) -> None:
        """Remove all key-value pairs from the store."""
        self._data.clear()
