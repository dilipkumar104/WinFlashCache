"""
test_cli.py — Unit tests for CLI parsing and subcommands configuration.
"""

import argparse
import pytest
from winflashcache.cli import build_parser, handle_save, handle_set, handle_get, handle_del, handle_exists, handle_keys, handle_count, handle_clear


def test_cli_parser_subcommands():
    """Verify that all subcommands are defined and map to the correct handler functions."""
    parser = build_parser()

    # Test 'set' subcommand
    args = parser.parse_args(["set", "key1", "value1"])
    assert args.command == "set"
    assert args.key == "key1"
    assert args.value == "value1"
    assert args.func == handle_set

    # Test 'get' subcommand
    args = parser.parse_args(["get", "key1"])
    assert args.command == "get"
    assert args.key == "key1"
    assert args.func == handle_get

    # Test 'del' subcommand
    args = parser.parse_args(["del", "key1"])
    assert args.command == "del"
    assert args.key == "key1"
    assert args.func == handle_del

    # Test 'exists' subcommand
    args = parser.parse_args(["exists", "key1"])
    assert args.command == "exists"
    assert args.key == "key1"
    assert args.func == handle_exists

    # Test 'keys' subcommand
    args = parser.parse_args(["keys"])
    assert args.command == "keys"
    assert args.func == handle_keys

    # Test 'count' subcommand
    args = parser.parse_args(["count"])
    assert args.command == "count"
    assert args.func == handle_count

    # Test 'clear' subcommand
    args = parser.parse_args(["clear"])
    assert args.command == "clear"
    assert args.func == handle_clear

    # Test 'save' subcommand
    args = parser.parse_args(["save"])
    assert args.command == "save"
    assert args.func == handle_save


def test_cli_parser_invalid_subcommand():
    """Verify that an invalid subcommand raises an error/exits."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["invalid_command"])
