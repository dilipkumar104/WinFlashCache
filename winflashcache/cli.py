"""
CLI module — Parses command-line arguments and routes them to handlers.

This module uses Python's built-in `argparse` library to define the commands
our application understands. Think of it as teaching the program English:

    python -m winflashcache set name Dilip
    python -m winflashcache get name
    python -m winflashcache del name

argparse breaks down the user's input into structured data we can work with.

Day 4 update: All handlers now catch custom exceptions and print clean,
user-friendly error messages to stderr with a non-zero exit code.
"""

import argparse
import sys

from winflashcache import __version__, __app_name__
from winflashcache.store import DataStore
from winflashcache.exceptions import WinFlashCacheError, KeyNotFoundError

# Instantiate our global storage engine
store = DataStore()


# =============================================================================
# ERROR HELPER
# =============================================================================

def _error(message: str, exit_code: int = 1) -> None:
    """
    Print a formatted error message to stderr and exit the process.

    We write errors to stderr (sys.stderr) rather than stdout because:
    - stdout is for program output (what you'd pipe or redirect).
    - stderr is for error messages (always shown to the user).
    This matters when users script with WinFlashCache:
        winflashcache get mykey >> output.txt
    Errors will still appear on screen, not pollute the output file.

    Args:
        message:   Human-readable error description.
        exit_code: Process exit code (non-zero signals failure to the OS).
    """
    print(f"(error) {message}", file=sys.stderr)
    sys.exit(exit_code)


# =============================================================================
# COMMAND HANDLER FUNCTIONS
# =============================================================================
# Each function below handles one CLI command, executing the corresponding
# operation on our DataStore instance and printing formatted results.
# Errors raised by the store are caught here and displayed cleanly.
# =============================================================================

def handle_set(args):
    """Handle the SET command — store a key-value pair."""
    try:
        store.set(args.key, args.value)
        print(f'SET "{args.key}" => "{args.value}"')
        print("OK")
    except WinFlashCacheError as exc:
        _error(str(exc))


def handle_get(args):
    """Handle the GET command — retrieve a value by its key."""
    try:
        val = store.get(args.key)
        print(f'"{val}"')
    except KeyNotFoundError as exc:
        # Use exit code 2 for "not found" — distinct from validation errors (1).
        _error(str(exc), exit_code=2)
    except WinFlashCacheError as exc:
        _error(str(exc))


def handle_del(args):
    """Handle the DEL command — delete a key-value pair."""
    try:
        existed = store.delete(args.key)
        if existed:
            print("(integer) 1")
        else:
            print("(integer) 0")
    except WinFlashCacheError as exc:
        _error(str(exc))


def handle_exists(args):
    """Handle the EXISTS command — check if a key is present."""
    try:
        found = store.exists(args.key)
        print("(boolean) true" if found else "(boolean) false")
    except WinFlashCacheError as exc:
        _error(str(exc))


def handle_keys(args):
    """Handle the KEYS command — list all stored keys."""
    all_keys = store.keys()
    if not all_keys:
        print("(empty list)")
    else:
        for idx, key in enumerate(all_keys, 1):
            print(f"{idx}) {key}")


def handle_count(args):
    """Handle the COUNT command — display the total number of keys."""
    print(f"(integer) {store.count()}")


def handle_clear(args):
    """Handle the CLEAR command — remove all stored data."""
    store.clear()
    print("OK - all data cleared.")


# =============================================================================
# ARGUMENT PARSER BUILDER
# =============================================================================

def build_parser():
    """Build and return the argument parser with all subcommands.

    This function creates a parser with the following command structure:

        winflashcache set <key> <value>   — Store a key-value pair
        winflashcache get <key>           — Retrieve a value
        winflashcache del <key>           — Delete a key
        winflashcache exists <key>        — Check if a key exists
        winflashcache keys                — List all keys
        winflashcache count               — Count stored keys
        winflashcache clear               — Remove all data

    Returns:
        argparse.ArgumentParser: The fully configured parser.
    """
    # ── Main parser ──────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        prog="winflashcache",
        description=f"{__app_name__} v{__version__} - A persistent CLI key-value store.",
        epilog="Example: winflashcache set name Dilip",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} v{__version__}",
    )

    # ── Subparsers ───────────────────────────────────────────────────────
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Available commands (use '<command> --help' for details)",
    )

    # ── SET ──────────────────────────────────────────────────────────────
    set_parser = subparsers.add_parser(
        "set",
        help="Store a key-value pair",
        description="Store a value under the given key. If the key already exists, its value is overwritten.",
    )
    set_parser.add_argument("key", help="The key to store (letters, digits, _, -, :, . only)")
    set_parser.add_argument("value", help="The value to associate with the key")
    set_parser.set_defaults(func=handle_set)

    # ── GET ──────────────────────────────────────────────────────────────
    get_parser = subparsers.add_parser(
        "get",
        help="Retrieve a value by key",
        description="Look up and display the value stored under the given key.",
    )
    get_parser.add_argument("key", help="The key to look up")
    get_parser.set_defaults(func=handle_get)

    # ── DEL ──────────────────────────────────────────────────────────────
    del_parser = subparsers.add_parser(
        "del",
        help="Delete a key-value pair",
        description="Remove the given key and its associated value from the store.",
    )
    del_parser.add_argument("key", help="The key to delete")
    del_parser.set_defaults(func=handle_del)

    # ── EXISTS ───────────────────────────────────────────────────────────
    exists_parser = subparsers.add_parser(
        "exists",
        help="Check if a key exists",
        description="Check whether the given key is present in the store.",
    )
    exists_parser.add_argument("key", help="The key to check")
    exists_parser.set_defaults(func=handle_exists)

    # ── KEYS ─────────────────────────────────────────────────────────────
    keys_parser = subparsers.add_parser(
        "keys",
        help="List all stored keys",
        description="Display every key currently in the store.",
    )
    keys_parser.set_defaults(func=handle_keys)

    # ── COUNT ────────────────────────────────────────────────────────────
    count_parser = subparsers.add_parser(
        "count",
        help="Show the number of stored keys",
        description="Display the total count of key-value pairs in the store.",
    )
    count_parser.set_defaults(func=handle_count)

    # ── CLEAR ────────────────────────────────────────────────────────────
    clear_parser = subparsers.add_parser(
        "clear",
        help="Remove all stored data",
        description="Delete every key-value pair from the store. This cannot be undone.",
    )
    clear_parser.set_defaults(func=handle_clear)

    return parser


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Parse arguments and dispatch to the appropriate command handler.

    This is the main entry point for the CLI. It:
    1. Builds the argument parser.
    2. Parses the user's input from sys.argv.
    3. Calls the matching handler function.
    4. Catches any unexpected exceptions as a last-resort safety net.

    If no command is given, it prints the help message.
    """
    parser = build_parser()
    args = parser.parse_args()

    # If the user typed just "winflashcache" with no command, show help.
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Dispatch to the handler. Any unhandled exception gets caught here
    # as an absolute last resort, so the user always gets a clean message.
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        _error(f"Unexpected error: {exc}", exit_code=99)
