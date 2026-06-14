"""
test_ttl.py — Unit tests for TTL (Time-To-Live) expiry support.

These tests verify:
  - The ttl helper functions (make_expiry, is_expired, remaining_ttl)
  - DataStore set() with TTL
  - Lazy expiry: expired keys are purged on next access
  - TTL persistence: expiry timestamps are saved and reloaded from disk
  - get_ttl() returns correct remaining time and -1 sentinel for no-expiry

Run:
    python -m pytest tests/test_ttl.py -v
"""

import json
import time
from pathlib import Path
import pytest

from winflashcache.ttl import make_expiry, is_expired, remaining_ttl
from winflashcache.store import DataStore
from winflashcache.exceptions import KeyNotFoundError


# =============================================================================
# TTL helper function tests
# =============================================================================

class TestMakeExpiry:
    def test_returns_future_timestamp(self):
        before = time.time()
        expiry = make_expiry(10)
        after = time.time()
        assert before + 10 <= expiry <= after + 10

    def test_zero_ttl_raises(self):
        with pytest.raises(ValueError, match="positive"):
            make_expiry(0)

    def test_negative_ttl_raises(self):
        with pytest.raises(ValueError, match="positive"):
            make_expiry(-5)

    def test_float_ttl_accepted(self):
        expiry = make_expiry(0.5)
        assert expiry > time.time()


class TestIsExpired:
    def test_future_timestamp_is_not_expired(self):
        future = time.time() + 100
        assert is_expired(future) is False

    def test_past_timestamp_is_expired(self):
        past = time.time() - 1
        assert is_expired(past) is True


class TestRemainingTTL:
    def test_future_timestamp_has_positive_remaining(self):
        future = time.time() + 10
        assert remaining_ttl(future) > 0

    def test_past_timestamp_returns_zero(self):
        past = time.time() - 10
        assert remaining_ttl(past) == 0.0


# =============================================================================
# DataStore TTL integration tests
# =============================================================================

class TestDataStoreTTL:
    def test_set_without_ttl_key_persists(self):
        store = DataStore()
        store.set("permanent", "value")
        assert store.get("permanent") == "value"

    def test_set_with_ttl_key_initially_accessible(self):
        store = DataStore()
        store.set("temp", "data", ttl=60)
        assert store.get("temp") == "data"

    def test_expired_key_raises_key_not_found_on_get(self):
        store = DataStore()
        # Set with a tiny TTL of 0.05 seconds
        store.set("fleeting", "gone", ttl=0.05)
        time.sleep(0.1)
        with pytest.raises(KeyNotFoundError):
            store.get("fleeting")

    def test_expired_key_returns_false_on_exists(self):
        store = DataStore()
        store.set("fleeting", "gone", ttl=0.05)
        time.sleep(0.1)
        assert store.exists("fleeting") is False

    def test_expired_key_excluded_from_keys(self):
        store = DataStore()
        store.set("permanent", "stays")
        store.set("fleeting", "gone", ttl=0.05)
        time.sleep(0.1)
        assert "fleeting" not in store.keys()
        assert "permanent" in store.keys()

    def test_expired_key_excluded_from_count(self):
        store = DataStore()
        store.set("permanent", "stays")
        store.set("fleeting", "gone", ttl=0.05)
        time.sleep(0.1)
        assert store.count() == 1

    def test_get_ttl_returns_none_for_no_expiry(self):
        store = DataStore()
        store.set("permanent", "value")
        assert store.get_ttl("permanent") is None

    def test_get_ttl_returns_positive_float_for_live_key(self):
        store = DataStore()
        store.set("temp", "value", ttl=60)
        ttl_remaining = store.get_ttl("temp")
        assert ttl_remaining is not None
        assert 0 < ttl_remaining <= 60

    def test_get_ttl_raises_for_missing_key(self):
        store = DataStore()
        with pytest.raises(KeyNotFoundError):
            store.get_ttl("nonexistent")

    def test_get_ttl_raises_for_expired_key(self):
        store = DataStore()
        store.set("fleeting", "gone", ttl=0.05)
        time.sleep(0.1)
        with pytest.raises(KeyNotFoundError):
            store.get_ttl("fleeting")

    def test_overwriting_key_removes_ttl_if_none_given(self):
        store = DataStore()
        store.set("key", "value", ttl=60)
        assert store.get_ttl("key") is not None
        # Overwrite without TTL
        store.set("key", "new_value")
        assert store.get_ttl("key") is None

    def test_overwriting_key_updates_ttl(self):
        store = DataStore()
        store.set("key", "value", ttl=10)
        store.set("key", "value", ttl=120)
        ttl_remaining = store.get_ttl("key")
        assert ttl_remaining is not None
        assert ttl_remaining > 60   # Should be closer to 120


# =============================================================================
# TTL persistence tests
# =============================================================================

class TestTTLPersistence:
    def test_ttl_survives_reload(self, tmp_path):
        """TTL expiry timestamps are saved to disk and restored on reload."""
        file_path = tmp_path / "store.json"
        store1 = DataStore(filepath=file_path)
        store1.set("session", "abc123", ttl=3600)

        # Verify the file contains TTL data
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        assert "ttl" in raw
        assert "session" in raw["ttl"]

        # Load a fresh store from the same file
        store2 = DataStore(filepath=file_path)
        assert store2.get("session") == "abc123"
        ttl_remaining = store2.get_ttl("session")
        assert ttl_remaining is not None
        assert 3590 < ttl_remaining <= 3600   # Should be close to 3600s

    def test_expired_key_not_loaded_if_past_expiry(self, tmp_path):
        """Keys whose TTL has already passed at load time are treated as missing."""
        file_path = tmp_path / "store.json"
        # Manually write a file with an expired TTL
        payload = {
            "data": {"old_key": "old_value"},
            "ttl": {"old_key": time.time() - 100}   # expired 100s ago
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        store = DataStore(filepath=file_path)
        with pytest.raises(KeyNotFoundError):
            store.get("old_key")
