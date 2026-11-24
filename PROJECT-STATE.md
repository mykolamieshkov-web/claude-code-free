# Project state - 2026-11-24

## Phase 1 completed in this handoff
- Reserved the approved Atom One Dark Pro palette in the project root as `PALETTE.md`.
- Preserved the supplied source files unchanged in `backups/stable-baseline-2026-11-24/`.
- Kept a working-copy snapshot under `project-config/` for subsequent edits.

## Approved next UI direction
- Remove spend/money display entirely.
- Add a compact Claude-inspired mascot immediately beside `CTX`.
- Display the model identifier in the same green as `Connected`.
- Show green `Connected` in normal operation; show warning/critical text only when those conditions occur.
- Keep compact context tiles and the request-quota bar.
- Preserve native Claude Code UI and existing API/Keychain data retrieval.

## Important implementation finding
The supplied `settings.json` points eight HTTP hooks at `127.0.0.1:19847`, but the user's diagnostics found no process listening on that port and no matching launchd service. The active statusline is a separate command invoking `openrouter-dashboard.py` every second. Do not treat hook connectivity as OpenRouter connectivity.

## Backup and GitHub
This snapshot is a local source backup suitable for committing to the project's Git repository. GitHub Pages is static site hosting, not the right mechanism for source-code backups. Use a Git commit/tag or a private/public repository release for versioned source backups. Review credentials before publishing; no API key was included in the supplied archive.
