"""
persistence.py — Handles reading and writing the store data to disk.

WHY A SEPARATE MODULE?
    The DataStore class handles in-memory logic. The persistence layer
    handles disk I/O. Keeping these two concerns separate means:
    - You can swap JSON for a binary format later without touching DataStore.
    - Tests for DataStore don't need a real disk at all.

FILE FORMAT: JSON
    We use Python's built-in `json` module — no extra libraries needed.
    The file looks like this:
        {
            "name": "Dilip",
            "lang": "Python",
            "project": "WinFlashCache"
        }

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
from typing import Dict


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

def save_to_disk(data: Dict[str, str], path: Path) -> None:
    """
    Write a key-value dictionary to a JSON file using an atomic write.

    The atomic write pattern prevents data corruption:
        1. Write to a temporary file in the same directory.
        2. Flush and sync to ensure data is fully written to disk.
        3. Rename the temp file over the target file (atomic operation).

    Args:
        data: The dictionary to serialize and save.
        path: The file path to write to.

    Raises:
        OSError: If the directory is not writable or the disk is full.
    """
    # Write to a temp file in the SAME directory as the target.
    # Same directory is important because rename() across different
    # filesystems/drives is NOT atomic.
    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)

    # NamedTemporaryFile gives us a unique temp filename automatically.
    # delete=False means the file persists after we close it so we can rename it.
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
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


def load_from_disk(path: Path) -> Dict[str, str]:
    """
    Read and deserialize a JSON file into a key-value dictionary.

    If the file does not exist, returns an empty dictionary — this is
    the expected state on first launch.

    Args:
        path: The file path to read from.

    Returns:
        A dict[str, str] of the stored key-value pairs, or {} if not found.

    Raises:
        ValueError: If the file exists but is not valid JSON.
        ValueError: If the JSON is valid but is not a flat string→string dict.
    """
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Store file '{path}' is corrupted (invalid JSON): {exc}"
        ) from exc

    # Validate that the loaded data is a flat string-to-string dict.
    # This guards against someone manually editing the file into a bad shape.
    if not isinstance(raw, dict):
        raise ValueError(
            f"Store file '{path}' has wrong format: expected a JSON object, "
            f"got {type(raw).__name__}."
        )

    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValueError(
                f"Store file '{path}' has non-string entry: {k!r}: {v!r}. "
                f"All keys and values must be strings."
            )

    return raw
