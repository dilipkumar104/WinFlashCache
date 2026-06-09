"""
Entry point for running WinFlashCache as a module.

This file is what Python executes when you run:
    python -m winflashcache

The `-m` flag tells Python: "Find the package named 'winflashcache',
look for a __main__.py inside it, and execute it."

Without this file, `python -m winflashcache` would give:
    "No module named winflashcache.__main__; 'winflashcache' is a package
    and cannot be directly executed"
"""

from winflashcache.cli import main

# This guard ensures main() only runs when the file is executed directly,
# not when it's imported by another module.
if __name__ == "__main__":
    main()
