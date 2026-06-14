"""
persistence.py — Handles reading and writing the store data to disk.

WHY A SEPARATE MODULE?
    The DataStore class handles in-memory logic. The persistence layer
    handles disk I/O. Keeping these two concerns separate means:
    - You can swap JSON for a binary format later without touching DataStore.
    - Tests for DataStore don't need a real disk at all.

FILE FORMAT: JSON (v2 — with TTL support)
    We use Python's built-in `json` module — no extra libraries needed.
    The file looks like this:
        {
            "data": {
                "name": "Dilip",
                "lang": "Python"
            },
            "ttl": {
                "session": 1718000000.0
            }
        }

    Keys without a TTL simply don't appear in the "ttl" dict.

    BACKWARD COMPATIBILITY:
        Old v1 files (a flat JSON object with no "data" key) are still
        supported. They are loaded as data-only with no TTL entries.

STORAGE LOCATION:
    Default: ~/.winflashcache/default.json
    The `~` expands to the user's home directory on any OS:
        Windows  → C:\\Users\\dilip\\.winflashcache\\default.json
        macOS    → /Users/dilip/.winflashcache/default.json
        Linux    → /home/dilip/.winflashcache/default.json

ATOMIC WRITES:
    A naive approach — open file, write data — is dangerous. If the program
    crashes mid-write, you get a half-written, corrupted file.

    We use a safer pattern called an "atomic write":
        1. Write the new data to a TEMP file (e.g. default.json.tmp)
        2. On success, RENAME the temp file over the real file.

    On all major OS, rename() is an atomic operation — it either fully
    succeeds or fully fails, never leaving a corrupted file behind.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Tuple


# ── Default storage path ───────────────────────────────────────────────────────

def get_default_store_path() -> Path:
    """
    Return the default path where WinFlashCache saves its data.

    Creates the parent directory if it does not exist.

    Returns:
        Path: ~/.winflashcache/default.json
    """
    store_dir = Path.home() / ".winflashcache"
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir / "default.json"


# ── Core I/O Functions ─────────────────────────────────────────────────────────

def save_to_disk(
    data: Dict[str, str],
    path: Path,
    ttl_data: Dict[str, float] = None,
) -> None:
    """
    Write a key-value dictionary (and optional TTL data) to a JSON file
    using an atomic write.

    The atomic write pattern prevents data corruption:
        1. Write to a temporary file in the same directory.
        2. Flush and sync to ensure data is fully written to disk.
        3. Rename the temp file over the target file (atomic operation).

    Args:
        data:     The key→value dictionary to serialize and save.
        path:     The file path to write to.
        ttl_data: Optional key→expiry_timestamp dictionary.

    Raises:
        OSError: If the directory is not writable or the disk is full.
    """
    if ttl_data is None:
        ttl_data = {}

    payload = {
        "data": data,
        "ttl": ttl_data,
    }

    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(payload, tmp_file, indent=2, ensure_ascii=False)
            tmp_file.write("\n")   # POSIX convention: end file with newline
            tmp_file.flush()
            os.fsync(tmp_file.fileno())   # Force OS to flush to physical disk
        # Atomic rename: replaces `path` with the temp file in one step
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file if anything went wrong
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_from_disk(path: Path) -> Tuple[Dict[str, str], Dict[str, float]]:
    """
    Read and deserialize a JSON file into a key-value dictionary and
    an optional TTL dictionary.

    If the file does not exist, returns empty dicts — this is the
    expected state on first launch.

    BACKWARD COMPATIBILITY:
        Old v1 files (flat JSON objects without a "data" key) are
        automatically detected and loaded as data-only with no TTL.

    Args:
        path: The file path to read from.

    Returns:
        A tuple: (data_dict, ttl_dict) where both are plain dicts.
        ttl_dict maps key→expiry_timestamp (float).

    Raises:
        ValueError: If the file exists but is not valid JSON.
        ValueError: If the JSON structure is not recognized.
    """
    if not path.exists():
        return {}, {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Store file '{path}' is corrupted (invalid JSON): {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise ValueError(
            f"Store file '{path}' has wrong format: expected a JSON object, "
            f"got {type(raw).__name__}."
        )

    # ── Detect v1 (flat) vs v2 (nested) format ────────────────────────────────
    if "data" in raw:
        # v2 format: { "data": {...}, "ttl": {...} }
        data = raw.get("data", {})
        ttl_data = raw.get("ttl", {})
    else:
        # v1 backward-compat: flat dict is treated as data-only
        data = raw
        ttl_data = {}

    # Validate data section
    if not isinstance(data, dict):
        raise ValueError(
            f"Store file '{path}': 'data' field must be a JSON object."
        )
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(
                f"Store file '{path}' has non-string entry: {k!r}: {v!r}. "
                f"All keys and values must be strings."
            )

    # Validate ttl section
    if not isinstance(ttl_data, dict):
        raise ValueError(
            f"Store file '{path}': 'ttl' field must be a JSON object."
        )
    for k, v in ttl_data.items():
        if not isinstance(k, str) or not isinstance(v, (int, float)):
            raise ValueError(
                f"Store file '{path}' has invalid TTL entry: {k!r}: {v!r}."
            )

    return data, {k: float(v) for k, v in ttl_data.items()}
