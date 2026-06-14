"""
ttl.py — Time-To-Live (TTL) management for WinFlashCache.

WHAT IS TTL?
    TTL stands for "Time-To-Live". It is a mechanism that automatically
    invalidates (expires) a key after a specified number of seconds.

    This is the same concept used by Redis:
        SET session "abc123" EX 3600   ← expires in 1 hour

    WinFlashCache uses it like:
        winflashcache set session abc123 --ttl 3600

HOW IT WORKS:
    When a key is set with a TTL, we record the UNIX timestamp at which
    the key should expire:
        expiry_time = time.time() + ttl_seconds

    On every read (GET, EXISTS, KEYS, COUNT), we check:
        if current_time > expiry_time:  → key is treated as deleted

    This is called "lazy expiry" — we don't run a background timer.
    Instead, expired keys are only cleaned up when accessed.

WHY LAZY EXPIRY?
    It's simple and requires no background threads. The tradeoff is that
    expired keys stay in memory and on disk until next accessed, but for
    a local CLI tool this is a perfectly acceptable design choice.

STORAGE FORMAT:
    TTL data is stored alongside key data in the JSON file:
        {
            "data": { "name": "Dilip", "session": "abc123" },
            "ttl":  { "session": 1718000000.0 }
        }

    Keys without a TTL simply don't appear in the "ttl" dict.
"""

import time
from typing import Dict, Optional


def make_expiry(ttl_seconds: float) -> float:
    """
    Calculate the absolute UNIX timestamp when a key should expire.

    Args:
        ttl_seconds: How many seconds from now the key should live.

    Returns:
        A float representing the expiry time as a UNIX timestamp.

    Raises:
        ValueError: If ttl_seconds is not a positive number.
    """
    if ttl_seconds <= 0:
        raise ValueError(
            f"TTL must be a positive number of seconds, got {ttl_seconds!r}."
        )
    return time.time() + ttl_seconds


def is_expired(expiry_timestamp: float) -> bool:
    """
    Check whether a given expiry timestamp has passed.

    Args:
        expiry_timestamp: The UNIX timestamp to check against current time.

    Returns:
        True if the key has expired, False if it is still alive.
    """
    return time.time() > expiry_timestamp


def remaining_ttl(expiry_timestamp: float) -> float:
    """
    Return the number of seconds remaining before a key expires.

    Args:
        expiry_timestamp: The UNIX timestamp when the key expires.

    Returns:
        Seconds remaining (positive) or 0 if already expired.
    """
    remaining = expiry_timestamp - time.time()
    return max(0.0, remaining)
