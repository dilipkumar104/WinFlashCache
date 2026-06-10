"""
CLI module — Parses command-line arguments and routes them to handlers.

This module uses Python's built-in `argparse` library to define the commands
our application understands. Think of it as teaching the program English:

    python -m winflashcache set name Dilip
    python -m winflashcache get name
    python -m winflashcache del name

argparse breaks down the user's input into structured data we can work with.
"""

import argparse
import sys

from winflashcache import __version__, __app_name__
from winflashcache.store import DataStore

# Instantiate our global storage engine
store = DataStore()


# =============================================================================
# COMMAND HANDLER FUNCTIONS
# =============================================================================
# Each function below handles one CLI command, executing the corresponding
# operation on our DataStore instance and printing formatted results.
# =============================================================================

def handle_set(args):
    """Handle the SET command — store a key-value pair."""
    store.set(args.key, args.value)
    print(f'SET "{args.key}" => "{args.value}"')
    print("OK")


def handle_get(args):
    """Handle the GET command — retrieve a value by its key."""
    val = store.get(args.key)
    if val is None:
        print("(nil)")
    else:
        print(f'"{val}"')


def handle_del(args):
    """Handle the DEL command — delete a key-value pair."""
    existed = store.delete(args.key)
    if existed:
        print("(integer) 1")
    else:
        print("(integer) 0")


def handle_exists(args):
    """Handle the EXISTS command — check if a key is present."""
    exists = store.exists(args.key)
    if exists:
        print("(boolean) true")
    else:
        print("(boolean) false")


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
    count = store.count()
    print(f"(integer) {count}")


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
    # This is the top-level parser. It defines the program name,
    # description, and the --version flag.
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
    # Subparsers let us define multiple commands under one program.
    # Instead of using flags like --set, we use positional subcommands:
    #     winflashcache set ...
    #     winflashcache get ...
    #
    # `dest="command"` means: store the chosen subcommand name in
    # `args.command` so we know which handler to call.
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
    set_parser.add_argument("key", help="The key to store")
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
    1. Builds the argument parser
    2. Parses the user's input from sys.argv
    3. Calls the matching handler function

    If no command is given, it prints the help message.
    """
    parser = build_parser()
    args = parser.parse_args()

    # If the user didn't type any command (just "winflashcache"),
    # show the help message and exit.
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Call the handler function that was attached via set_defaults(func=...).
    # This is the "dispatch" pattern — instead of a big if/elif chain,
    # each subparser knows which function to call.
    args.func(args)
