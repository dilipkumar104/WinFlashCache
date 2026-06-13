"""
test_persistence.py — Unit tests for the file persistence module.

These tests verify that we can save to and load from disk, handle
edge cases like missing/corrupted files, and ensure that DataStore
automatically integrates with file serialization.
"""

import json
import os
from pathlib import Path
import pytest

from winflashcache.exceptions import KeyValidationError
from winflashcache.persistence import (
    get_default_store_path,
    save_to_disk,
    load_from_disk,
)
from winflashcache.store import DataStore


def test_get_default_store_path():
    """Verify that get_default_store_path returns a path in the home directory."""
    path = get_default_store_path()
    assert isinstance(path, Path)
    assert path.name == "default.json"
    assert path.parent.name == ".winflashcache"
    assert path.parent.exists()


def test_save_and_load_success(tmp_path):
    """Test standard save and load operations with a valid dictionary."""
    file_path = tmp_path / "store.json"
    data = {"key1": "value1", "key2": "value2"}

    save_to_disk(data, file_path)
    assert file_path.exists()

    loaded_data = load_from_disk(file_path)
    assert loaded_data == data


def test_load_non_existent_file_returns_empty_dict(tmp_path):
    """Loading a file that does not exist should return an empty dict."""
    file_path = tmp_path / "non_existent.json"
    assert load_from_disk(file_path) == {}


def test_load_corrupted_json_raises_value_error(tmp_path):
    """Loading a file with invalid JSON should raise ValueError."""
    file_path = tmp_path / "corrupted.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{invalid_json:")

    with pytest.raises(ValueError, match="is corrupted"):
        load_from_disk(file_path)


def test_load_non_dict_json_raises_value_error(tmp_path):
    """Loading a file that is valid JSON but not a JSON object should raise ValueError."""
    file_path = tmp_path / "list.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(["item1", "item2"], f)

    with pytest.raises(ValueError, match="expected a JSON object"):
        load_from_disk(file_path)


def test_load_non_string_dict_raises_value_error(tmp_path):
    """Loading a JSON object that has non-string values should raise ValueError."""
    file_path = tmp_path / "bad_types.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"key": 123}, f)

    with pytest.raises(ValueError, match="All keys and values must be strings"):
        load_from_disk(file_path)


def test_datastore_persistence_integration(tmp_path):
    """Verify DataStore automatically loads from and saves to the configured file."""
    file_path = tmp_path / "db.json"

    # 1. Start with an empty file/store
    store1 = DataStore(filepath=file_path)
    assert store1.count() == 0

    # 2. Mutating operations should save automatically (write-through)
    store1.set("name", "Dilip")
    assert file_path.exists()

    # Load file contents directly to verify it was written correctly
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {"name": "Dilip"}

    # 3. Initialize a new store with the same path, verify it loads automatically
    store2 = DataStore(filepath=file_path)
    assert store2.get("name") == "Dilip"

    # 4. Delete should save automatically
    store2.delete("name")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {}

    # 5. Set and clear should save automatically
    store2.set("age", "20")
    store2.clear()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {}


def test_datastore_save_load_explicit_calls(tmp_path):
    """Verify explicit save() and load() methods on DataStore work as expected."""
    file_path = tmp_path / "explicit.json"
    store = DataStore()
    store.set("foo", "bar")

    # Should not write to disk yet since filepath is None
    assert not file_path.exists()

    # Explicit save with path
    store.save(filepath=file_path)
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        assert json.load(f) == {"foo": "bar"}

    # Modify in-memory store
    store.set("foo", "baz")
    assert store.get("foo") == "baz"

    # Explicit load with path to restore previous state
    store.load(filepath=file_path)
    assert store.get("foo") == "bar"
