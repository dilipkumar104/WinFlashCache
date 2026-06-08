<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/status-In%20Development-orange" alt="Status"/>
</p>

# ⚡ WinFlashCache

> A lightweight, persistent CLI key-value store — think **local Redis** for your terminal.

WinFlashCache lets you **store**, **retrieve**, and **delete** data using simple key-value commands. All data is persisted to disk, so your cache survives terminal restarts, reboots, and even system crashes.

---

## 🎯 Project Goals

| Goal | Description |
|------|-------------|
| **Persistence** | Data survives across sessions — no in-memory-only volatility. |
| **Speed** | Sub-millisecond reads and writes for typical workloads. |
| **Simplicity** | A dead-simple CLI interface anyone can pick up in seconds. |
| **Zero Dependencies** | Runs on the Python standard library alone (no Redis, no SQLite drivers to install). |
| **Portability** | Works on Windows, macOS, and Linux out of the box. |

---

## ✨ Features

### Core (v1.0)
- `SET <key> <value>` — Store a key-value pair.
- `GET <key>` — Retrieve a value by key.
- `DEL <key>` — Delete a key-value pair.
- `EXISTS <key>` — Check if a key exists.
- `KEYS [pattern]` — List all keys, optionally filtered by a glob pattern.
- `CLEAR` — Remove all stored data.
- `COUNT` — Return the total number of stored keys.
- `EXPORT [file]` — Export all data to a JSON file.
- `IMPORT <file>` — Import data from a JSON file.

### Planned (v2.0+)
- **TTL / Expiry** — Auto-expire keys after a configurable duration.
- **Namespaces** — Logically group keys under named scopes.
- **Batch Operations** — `MSET` / `MGET` for bulk reads and writes.
- **Watch / Subscribe** — Filesystem-based change notifications.
- **Encryption at Rest** — AES-256 encrypted storage backend.
- **HTTP API Mode** — Optional lightweight HTTP server for programmatic access.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│                 CLI Interface                │
│          (argparse / REPL loop)              │
├──────────────────────────────────────────────┤
│              Command Router                  │
│     Parses commands → dispatches actions     │
├──────────────────────────────────────────────┤
│             Storage Engine                   │
│   In-memory dict ←→ Disk persistence         │
│   (JSON / binary flat-file backend)          │
├──────────────────────────────────────────────┤
│              File System                     │
│     ~/.winflashcache/default.json            │
└──────────────────────────────────────────────┘
```

**Design Principles:**
- **Lazy Loading** — Data is loaded into memory on first access, not on startup.
- **Write-Through** — Every mutation is immediately flushed to disk.
- **Atomic Writes** — Uses temp-file + rename to prevent corruption on crash.
- **Single-File Store** — One JSON file per namespace for simplicity.

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/WinFlashCache.git
cd WinFlashCache

# (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install in development mode
pip install -e .
```

---

## 🚀 Usage

### Interactive REPL Mode

```bash
$ winflashcache
WinFlashCache v1.0.0 — Type 'HELP' for commands, 'EXIT' to quit.

wfc> SET name "Dilip"
OK

wfc> SET lang "Python"
OK

wfc> GET name
"Dilip"

wfc> KEYS
1) name
2) lang

wfc> COUNT
(integer) 2

wfc> DEL lang
(integer) 1

wfc> EXISTS lang
(boolean) false

wfc> EXIT
Goodbye!
```

### Single-Command Mode

```bash
$ winflashcache set api_key "sk-abc123"
OK

$ winflashcache get api_key
"sk-abc123"

$ winflashcache keys
1) name
2) api_key
```

---

## 🗂️ Project Structure

```
WinFlashCache/
├── winflashcache/          # Main package
│   ├── __init__.py
│   ├── __main__.py         # Entry point (python -m winflashcache)
│   ├── cli.py              # CLI argument parsing & REPL
│   ├── commands.py         # Command implementations
│   ├── store.py            # Storage engine (read/write/persist)
│   └── utils.py            # Helpers (formatting, validation)
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_commands.py
│   ├── test_store.py
│   └── test_cli.py
├── .gitignore
├── README.md
├── LICENSE
├── pyproject.toml          # PEP 621 project metadata
└── setup.cfg               # Optional legacy config
```

---

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=winflashcache --cov-report=term-missing
```

---

## 🛣️ Roadmap

- [x] Project setup (repo, README, .gitignore)
- [ ] Core storage engine with JSON persistence
- [ ] CLI with argparse (single-command mode)
- [ ] Interactive REPL mode
- [ ] Full command set (SET, GET, DEL, EXISTS, KEYS, CLEAR, COUNT)
- [ ] EXPORT / IMPORT commands
- [ ] Comprehensive test suite
- [ ] PyPI packaging (`pip install winflashcache`)
- [ ] TTL / key expiry support
- [ ] Namespace support
- [ ] Encryption at rest

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Built with ☕ and determination.
</p>
