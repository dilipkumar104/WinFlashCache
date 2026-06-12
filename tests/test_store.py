"""
test_store.py — Unit tests for the DataStore in-memory storage engine.

Each test class groups related behaviour, and each test method covers
one specific scenario (the "one assertion per test" principle keeps
failures easy to diagnose).

How to read a test:
    - ARRANGE  : set up the objects needed for the test.
    - ACT      : call the method being tested.
    - ASSERT   : check the result is what we expect.

Run these tests:
    python -m pytest tests/test_store.py -v
"""

import pytest

from winflashcache.store import DataStore
from winflashcache.exceptions import (
    KeyNotFoundError,
    KeyValidationError,
    ValueValidationError,
)


# =============================================================================
# FIXTURES
# =============================================================================
# A pytest "fixture" is a reusable setup function. Instead of creating a new
# DataStore manually inside every test, we declare it once here and pytest
# injects it automatically into any test that lists `store` as a parameter.
# =============================================================================

@pytest.fixture
def store() -> DataStore:
    """Return a fresh, empty DataStore for each test."""
    return DataStore()


@pytest.fixture
def populated_store() -> DataStore:
    """Return a DataStore pre-loaded with three key-value pairs."""
    ds = DataStore()
    ds.set("name", "Dilip")
    ds.set("lang", "Python")
    ds.set("project", "WinFlashCache")
    return ds


# =============================================================================
# SET TESTS
# =============================================================================

class TestSet:
    """Tests for DataStore.set()"""

    def test_set_stores_a_value(self, store):
        """A value placed with set() can be retrieved with get()."""
        # Arrange + Act
        store.set("colour", "blue")
        # Assert
        assert store.get("colour") == "blue"

    def test_set_overwrites_existing_key(self, store):
        """Setting an existing key updates its value."""
        store.set("colour", "blue")
        store.set("colour", "red")         # Overwrite
        assert store.get("colour") == "red"

    def test_set_accepts_alphanumeric_key(self, store):
        """Keys with letters and digits are accepted."""
        store.set("key123", "value")
        assert store.get("key123") == "value"

    def test_set_accepts_key_with_underscores_and_dots(self, store):
        """Keys with underscores, dots, hyphens, and colons are accepted."""
        store.set("app.setting-1:dev", "enabled")
        assert store.get("app.setting-1:dev") == "enabled"

    def test_set_raises_for_empty_key(self, store):
        """An empty key raises KeyValidationError."""
        with pytest.raises(KeyValidationError):
            store.set("", "value")

    def test_set_raises_for_key_with_spaces(self, store):
        """A key containing spaces raises KeyValidationError."""
        with pytest.raises(KeyValidationError):
            store.set("my key", "value")

    def test_set_raises_for_key_too_long(self, store):
        """A key exceeding 128 characters raises KeyValidationError."""
        long_key = "k" * 129
        with pytest.raises(KeyValidationError):
            store.set(long_key, "value")

    def test_set_raises_for_empty_value(self, store):
        """An empty value raises ValueValidationError."""
        with pytest.raises(ValueValidationError):
            store.set("key", "")

    def test_set_raises_for_value_too_long(self, store):
        """A value exceeding 512 characters raises ValueValidationError."""
        long_value = "x" * 513
        with pytest.raises(ValueValidationError):
            store.set("key", long_value)

    def test_set_increments_count(self, store):
        """count() increases by 1 after each unique set()."""
        assert store.count() == 0
        store.set("a", "1")
        assert store.count() == 1
        store.set("b", "2")
        assert store.count() == 2

    def test_set_overwrite_does_not_increment_count(self, store):
        """Overwriting an existing key does not increase count."""
        store.set("a", "1")
        store.set("a", "2")          # Overwrite, not a new key
        assert store.count() == 1


# =============================================================================
# GET TESTS
# =============================================================================

class TestGet:
    """Tests for DataStore.get()"""

    def test_get_returns_stored_value(self, populated_store):
        """get() returns the correct value for a known key."""
        assert populated_store.get("name") == "Dilip"

    def test_get_returns_correct_value_for_each_key(self, populated_store):
        """get() returns distinct values for distinct keys."""
        assert populated_store.get("lang") == "Python"
        assert populated_store.get("project") == "WinFlashCache"

    def test_get_raises_for_missing_key(self, store):
        """get() raises KeyNotFoundError when the key does not exist."""
        with pytest.raises(KeyNotFoundError) as exc_info:
            store.get("ghost")
        # Also check the error message mentions the key name
        assert "ghost" in str(exc_info.value)

    def test_get_raises_for_deleted_key(self, populated_store):
        """get() raises KeyNotFoundError after the key has been deleted."""
        populated_store.delete("name")
        with pytest.raises(KeyNotFoundError):
            populated_store.get("name")

    def test_get_raises_for_invalid_key(self, store):
        """get() raises KeyValidationError for an invalid key format."""
        with pytest.raises(KeyValidationError):
            store.get("bad key!")

    def test_get_is_case_sensitive(self, store):
        """Keys are case-sensitive — 'Name' and 'name' are different keys."""
        store.set("name", "lower")
        store.set("Name", "upper")
        assert store.get("name") == "lower"
        assert store.get("Name") == "upper"


# =============================================================================
# DELETE TESTS
# =============================================================================

class TestDelete:
    """Tests for DataStore.delete()"""

    def test_delete_removes_existing_key(self, populated_store):
        """delete() removes the key so it no longer exists."""
        populated_store.delete("name")
        assert not populated_store.exists("name")

    def test_delete_returns_true_for_existing_key(self, populated_store):
        """delete() returns True when the key was present."""
        result = populated_store.delete("name")
        assert result is True

    def test_delete_returns_false_for_missing_key(self, store):
        """delete() returns False when the key was not in the store."""
        result = store.delete("ghost")
        assert result is False

    def test_delete_decrements_count(self, populated_store):
        """count() decreases by 1 after a successful delete()."""
        before = populated_store.count()
        populated_store.delete("name")
        assert populated_store.count() == before - 1

    def test_delete_missing_key_does_not_change_count(self, populated_store):
        """Deleting a missing key leaves count unchanged."""
        before = populated_store.count()
        populated_store.delete("nonexistent")
        assert populated_store.count() == before

    def test_delete_raises_for_invalid_key(self, store):
        """delete() raises KeyValidationError for an invalid key format."""
        with pytest.raises(KeyValidationError):
            store.delete("")


# =============================================================================
# EXISTS TESTS
# =============================================================================

class TestExists:
    """Tests for DataStore.exists()"""

    def test_exists_returns_true_for_present_key(self, populated_store):
        """exists() returns True when the key is in the store."""
        assert populated_store.exists("name") is True

    def test_exists_returns_false_for_absent_key(self, store):
        """exists() returns False when the key is not in the store."""
        assert store.exists("ghost") is False

    def test_exists_returns_false_after_delete(self, populated_store):
        """exists() returns False after the key has been deleted."""
        populated_store.delete("name")
        assert populated_store.exists("name") is False

    def test_exists_raises_for_invalid_key(self, store):
        """exists() raises KeyValidationError for an invalid key."""
        with pytest.raises(KeyValidationError):
            store.exists("bad key!")


# =============================================================================
# KEYS TESTS
# =============================================================================

class TestKeys:
    """Tests for DataStore.keys()"""

    def test_keys_empty_store_returns_empty_list(self, store):
        """keys() returns an empty list when the store has no entries."""
        assert store.keys() == []

    def test_keys_returns_all_keys(self, populated_store):
        """keys() returns all stored key names."""
        result = populated_store.keys()
        assert set(result) == {"name", "lang", "project"}

    def test_keys_returns_sorted_list(self, store):
        """keys() returns keys in sorted (alphabetical) order."""
        store.set("zebra", "1")
        store.set("apple", "2")
        store.set("mango", "3")
        assert store.keys() == ["apple", "mango", "zebra"]

    def test_keys_does_not_include_deleted_key(self, populated_store):
        """A deleted key does not appear in keys()."""
        populated_store.delete("name")
        assert "name" not in populated_store.keys()


# =============================================================================
# COUNT TESTS
# =============================================================================

class TestCount:
    """Tests for DataStore.count()"""

    def test_count_is_zero_on_empty_store(self, store):
        """count() returns 0 for a brand-new store."""
        assert store.count() == 0

    def test_count_matches_number_of_keys(self, populated_store):
        """count() returns the exact number of keys in the store."""
        assert populated_store.count() == 3

    def test_count_after_overwrite_is_unchanged(self, store):
        """Overwriting a key does not change count."""
        store.set("x", "1")
        store.set("x", "2")
        assert store.count() == 1


# =============================================================================
# CLEAR TESTS
# =============================================================================

class TestClear:
    """Tests for DataStore.clear()"""

    def test_clear_empties_the_store(self, populated_store):
        """clear() removes all keys."""
        populated_store.clear()
        assert populated_store.count() == 0

    def test_clear_makes_keys_return_empty_list(self, populated_store):
        """After clear(), keys() returns an empty list."""
        populated_store.clear()
        assert populated_store.keys() == []

    def test_clear_on_empty_store_does_not_raise(self, store):
        """Calling clear() on an already-empty store is safe."""
        store.clear()          # Should not raise any exception
        assert store.count() == 0

    def test_can_set_after_clear(self, populated_store):
        """The store is still usable after being cleared."""
        populated_store.clear()
        populated_store.set("fresh", "start")
        assert populated_store.get("fresh") == "start"
