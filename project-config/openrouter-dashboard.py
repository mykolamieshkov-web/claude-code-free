#!/usr/bin/env python3
"""Install a multi-line OpenRouter dashboard for Claude Code on macOS.

Run: python3 setup-openrouter-dashboard.py
The installed file is also the statusline program; Claude Code invokes it with
--statusline and supplies session JSON on stdin.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"
SETTINGS = CLAUDE / "settings.json"
DASHBOARD = CLAUDE / "openrouter-dashboard.py"
OLD_STATUSLINE = CLAUDE / "openrouter-statusline.sh"
LAUNCHER = HOME / ".local/bin/claude-free"
CACHE_DIR = HOME / "Library/Caches/claude-openrouter-statusline"
CACHE = CACHE_DIR / "usage.json"
KEYCHAIN_SERVICE = "claude-free-openrouter"
USAGE_URL = "https://openrouter.ai/api/v1/key"

R = "\033[0m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
PURPLE = "\033[35m"
GREY = "\033[90m"
WHITE = "\033[97m"

ALIASES = {
    "particle-ai/particle-1:free": "coder-1:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free": "nemotron-3-ultra:free",
}


def get_key():
    try:
        p = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-a",
             os.environ.get("USER", ""), "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=3, check=True)
        return p.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def read_cache():
    try:
        obj = json.loads(CACHE.read_text())
        if isinstance(obj.get("data"), dict):
            return obj
    except (OSError, ValueError, AttributeError):
        pass
    return None


def fetch_usage():
    key = get_key()
    if not key:
        return None, "OpenRouter Keychain credential unavailable"
    req = urllib.request.Request(
        USAGE_URL, headers={"Authorization": "Bearer " + key,
                            "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            obj = json.loads(response.read().decode())
        quota = obj.get("data", {}).get("free_model_daily_requests")
        if not isinstance(quota, dict) or any(
            not isinstance(quota.get(k), (int, float))
            for k in ("used", "limit", "remaining")
        ):
            return None, "OpenRouter quota data not reported"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_name(CACHE.name + ".tmp")
        tmp.write_text(json.dumps(obj))
        os.replace(tmp, CACHE)
        return obj, None
    except urllib.error.HTTPError as e:
        return None, f"OpenRouter returned HTTP {e.code}"
    except (OSError, urllib.error.URLError, TimeoutError, ValueError):
        return None, "OpenRouter usage endpoint unavailable"
    finally:
        key = None


def usage_data():
    cached = read_cache()
    try:
        age = time.time() - CACHE.stat().st_mtime
    except OSError:
        age = 10**9
    if cached and age < 60:
        return cached, None
    fresh, error = fetch_usage()
    if fresh:
        return fresh, None
    if cached:
        return cached, "Showing cached quota; refresh failed"
    return None, error


def integer(v):
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 else None


def reset_countdown():
    # OpenRouter's free-model daily quota resets at 00:00 UTC.
    now = dt.datetime.now(dt.timezone.utc)
    next_reset = dt.datetime.combine(
        (now + dt.timedelta(days=1)).date(), dt.time.min,
        tzinfo=dt.timezone.utc)
    seconds = max(0, int((next_reset - now).total_seconds()))
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours:
        return f"Resets in {hours}h {minutes:02d}m"
    if minutes:
        return f"Resets in {minutes}m"
    return "Resets in less than 1m"


def bar(pct, width=12):
    n = max(0, min(width, round(pct * width / 100)))
    return "━" * n + "─" * (width - n)


def render(raw):
    try:
        d = json.loads(raw)
        if not isinstance(d, dict):
            raise ValueError()
    except (ValueError, TypeError):
        print("OpenRouter dashboard · waiting for session data")
        return

    model = d.get("model") or {}
    mid = str(model.get("id") or "")
    label = ALIASES.get(mid, str(model.get("display_name") or mid or "Claude Code"))
    label = ALIASES.get(label, label)

    ctx = d.get("context_window") or {}
    pct = integer(ctx.get("used_percentage"))
    pct = min(100, pct) if pct is not None else None
    capacity = integer(ctx.get("context_window_size"))
    tokens = integer(ctx.get("total_input_tokens"))

    obj, note = usage_data()
    quota = (obj or {}).get("data", {}).get("free_model_daily_requests", {})
    used, limit, remaining = (integer(quota.get(k)) for k in
                              ("used", "limit", "remaining"))
    valid_quota = used is not None and limit not in (None, 0) and remaining is not None
    upct = min(100, round(used * 100 / limit)) if valid_quota else None

    # A brief readiness confirmation is shown once per Claude Code session.
    # It disappears on subsequent statusline refreshes so it cannot compete
    # with the agentic workflow. A known exhausted quota remains a persistent
    # critical warning. This statusline cannot inspect arbitrary hook/tool errors.
    session_id = str(d.get("session_id") or "default-session")
    safe_session = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
    ready_marker = CACHE_DIR / f"ready-{safe_session[:100]}.seen"
    critical_quota = valid_quota and remaining == 0

    if critical_quota:
        health = f"{RED}● QUOTA EXHAUSTED{R}"
    elif valid_quota and not ready_marker.exists():
        health = f"{GREEN}● YOU'RE GOOD TO GO{R}"
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            ready_marker.touch()
        except OSError:
            pass
    elif not valid_quota and pct is None:
        health = f"{YELLOW}● STATUS UNKNOWN{R}"
    else:
        health = ""

    print(f"{WHITE}OPENROUTER{R}" + (f"  {health}" if health else ""))
    print(f"{DIM}MODEL: {label}{R}")
    print(f"{WHITE}USAGE ESTIMATE{R}                                      {WHITE}CONTEXT{R}")

    if valid_quota:
        qcolor = RED if remaining == 0 else YELLOW if remaining <= 5 else GREEN
        left1 = f"{qcolor}{upct:>3}%  {bar(upct)}{R}"
        left2 = f"{DIM}{used}/{limit} requests used · {remaining} remaining{R}"
        left3 = f"{RED}CRITICAL: daily free-model quota exhausted{R}" if remaining == 0 else f"{DIM}{reset_countdown()}{R}"
    else:
        left1 = f"{YELLOW}Quota unavailable{R}"
        left2 = f"{DIM}{note or 'Quota data not reported'}{R}"
        left3 = ""

    if pct is not None:
        right1 = f"{PURPLE}{pct:>3}%{R}"
        filled = round(pct * 40 / 100)
        grid = []
        for row in range(4):
            grid.append(" ".join(
                f"{PURPLE}██{R}" if row * 10 + col < filled else f"{GREY}██{R}"
                for col in range(10)))
        right2 = f"{tokens:,}" if tokens is not None else "Token count unavailable"
        right3 = f"{capacity:,} tokens capacity" if capacity is not None else "Context capacity unavailable"
    else:
        right1, right2, right3, grid = f"{YELLOW}Waiting for context data{R}", "", "", []

    # A stable two-column layout, using ANSI-aware padding by keeping columns
    # deliberately compact. Narrow terminals naturally wrap rather than truncate.
    print(f"{left1}                         {right1}")
    print(f"{left2}                         {DIM}{right2}{R}")
    if left3:
        print(left3)
    for line in grid:
        print("                         " + line)
    if right3:
        print("                         " + f"{DIM}{right3}{R}")
        print("                         " + f"{DIM}Estimated context occupancy{R}")


def backup(path, dest):
    if path.exists():
        shutil.copy2(path, dest / (path.name + ".bak"))


def install():
    if sys.platform != "darwin":
        raise RuntimeError("This installer is intended for macOS.")
    if not SETTINGS.is_file():
        raise RuntimeError(f"Existing settings file not found: {SETTINGS}")
    settings = json.loads(SETTINGS.read_text())
    if not isinstance(settings, dict):
        raise RuntimeError("settings.json must contain a JSON object.")

    # Validate the statusline logic offline before touching user files.
    assert ALIASES["particle-ai/particle-1:free"] == "coder-1:free"
    assert bar(50).count("━") == 6
    assert reset_countdown().startswith("Resets in ")

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = CLAUDE / "backups" / f"openrouter-dashboard-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    for p in (SETTINGS, LAUNCHER, OLD_STATUSLINE, DASHBOARD):
        backup(p, backup_dir)

    source = Path(__file__).resolve()
    tmp_dashboard = DASHBOARD.with_suffix(".py.tmp")
    shutil.copy2(source, tmp_dashboard)
    os.replace(tmp_dashboard, DASHBOARD)
    DASHBOARD.chmod(0o700)

    # Only statusLine is changed. All hooks and other settings are preserved.
    settings["statusLine"] = {
        "type": "command",
        "command": f'/usr/bin/python3 "{DASHBOARD}" --statusline',
        "padding": 1,
        "refreshInterval": 1,
    }
    fd, tmp_name = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=CLAUDE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
        # Parse the staged file before atomic replacement.
        json.loads(Path(tmp_name).read_text(encoding="utf-8"))
        os.chmod(tmp_name, SETTINGS.stat().st_mode & 0o777)
        os.replace(tmp_name, SETTINGS)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print("Dashboard installed.")
    print(f"Backup: {backup_dir}")
    print(f"Statusline: {DASHBOARD}")
    print("Preserved: launcher, Keychain credential, hooks, and all other settings.")
    print("Refresh: dashboard 1s; OpenRouter quota request no more than once per 60s.")
    print("Restart Claude Code to load the updated dashboard.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--statusline", action="store_true")
    args = parser.parse_args()
    if args.statusline:
        render(sys.stdin.read())
    else:
        install()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
