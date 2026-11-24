# Stable baseline backup

This directory contains an unchanged copy of the three files supplied for the current project audit on 2026-11-24.

It is a source snapshot, not a verified runnable release. The settings file contains historical HTTP hooks pointing to `127.0.0.1:19847`; the user machine showed no listener on that port during the audit. Do not assume those hooks are operational.

The active statusline command in the supplied settings invokes `~/.claude/openrouter-dashboard.py`. The dashboard source itself contains the current Keychain lookup, OpenRouter quota request/cache, context payload parsing, and old two-column renderer.

Before installing any later version on the user's Mac:
1. Back up the live `~/.claude/settings.json` and `~/.claude/openrouter-dashboard.py` on that machine.
2. Run offline renderer tests against representative Claude Code JSON payloads.
3. Confirm the generated statusline output does not exceed the terminal width and does not leak literal ANSI escape notation.
4. Keep hooks, Keychain access, API retrieval, and model configuration unchanged unless explicitly approved.
