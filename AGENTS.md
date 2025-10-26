# Bookerics Agent Guide

## Commands
- **Run app**: `uv run bookerics`
- **Type check**: `pyright` (standard mode with unused/duplicate import warnings)
- **Format**: `isort` (black profile, line length 88) - no built-in formatter command found
- No tests found in codebase

## Architecture
- **Framework**: FastHTML (previously Ludic) + HTMX for dynamic interactions
- **Database**: SQLite (`bookerics.db`) with thread-local connections
- **Structure**: `bookerics/` module with main.py (app entry), routes.py, database.py, components.py, ai.py, utils.py
- **web hosting with SFTP SFTP**: Auto-uploads screenshots and RSS feeds (`bookerics/feeds/`) via SFTP to web hosting with SFTP server
- **OpenAI**: AI-powered tag generation when user submits without tags
- **Screenshots**: Uses `shot-scraper` to capture website thumbnails

## Code Style
- **Python 3.13+** with strict type checking (mypy strict mode)
- **Imports**: isort with black profile, combine_as_imports=true, trailing commas
- **Components**: FastHTML components (Div, A, Input, etc.) with dict attrs like `{'hx_get': '/search'}`
- **Async**: Use asyncssh, aiohttp, aiofiles for I/O operations
- **Logging**: Use `utils.logger` for debugging
- **Debugging**: Add copious print statements during troubleshooting for easy copy-paste feedback
