#!/bin/bash
set -u

CACHE_DIR="$HOME/Library/Caches/claude-openrouter-statusline"
CACHE_FILE="$CACHE_DIR/usage.json"
mkdir -p "$CACHE_DIR"

INPUT="$(cat)"
MODEL="$(printf '%s' "$INPUT" | jq -r '.model.display_name // .model.id // "Claude Code"' 2>/dev/null)"
[ -n "$MODEL" ] || MODEL="Claude Code"

# Refresh the cached OpenRouter quota at most once every 60 seconds.
NOW="$(date +%s)"
CACHE_MTIME=0
if [ -f "$CACHE_FILE" ]; then
  CACHE_MTIME="$(stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)"
fi

if [ ! -s "$CACHE_FILE" ] || [ $((NOW - CACHE_MTIME)) -ge 60 ]; then
  KEY="$(security find-generic-password \
    -a "$USER" \
    -s "claude-free-openrouter" \
    -w 2>/dev/null || true)"

  if [ -n "$KEY" ]; then
    RESPONSE="$(curl -fsS --connect-timeout 2 --max-time 4 \
      -H "Authorization: Bearer $KEY" \
      https://openrouter.ai/api/v1/key 2>/dev/null || true)"
    unset KEY

    if printf '%s' "$RESPONSE" | jq -e '
      .data.free_model_daily_requests
      | (.used | numbers) and (.limit | numbers) and (.remaining | numbers)
    ' >/dev/null 2>&1; then
      TMP_FILE="$CACHE_FILE.tmp.$$"
      printf '%s\n' "$RESPONSE" > "$TMP_FILE" && mv "$TMP_FILE" "$CACHE_FILE"
    fi
    unset RESPONSE
  fi
fi

if [ -s "$CACHE_FILE" ]; then
  USED="$(jq -r '.data.free_model_daily_requests.used' "$CACHE_FILE" 2>/dev/null || echo '?')"
  LIMIT="$(jq -r '.data.free_model_daily_requests.limit' "$CACHE_FILE" 2>/dev/null || echo '?')"
  REMAINING="$(jq -r '.data.free_model_daily_requests.remaining' "$CACHE_FILE" 2>/dev/null || echo '?')"

  if [[ "$USED" =~ ^[0-9]+$ && "$LIMIT" =~ ^[0-9]+$ && "$REMAINING" =~ ^[0-9]+$ && "$LIMIT" -gt 0 ]]; then
    PCT=$(( USED * 100 / LIMIT ))
    FILLED=$(( PCT * 12 / 100 ))
    BAR=""
    for ((i=0; i<12; i++)); do
      if [ "$i" -lt "$FILLED" ]; then BAR+="█"; else BAR+="░"; fi
    done

    if [ "$REMAINING" -eq 0 ]; then COLOR=$'\033[31m'
    elif [ "$REMAINING" -le 5 ]; then COLOR=$'\033[31m'
    elif [ "$REMAINING" -le 15 ]; then COLOR=$'\033[33m'
    else COLOR=$'\033[32m'
    fi
    RESET=$'\033[0m'
    DIM=$'\033[2m'

    printf '%s\n' "${DIM}OpenRouter FREE${RESET} · ${MODEL}"
    printf '%s\n' "${COLOR}${BAR}${RESET} ${USED}/${LIMIT} used · ${COLOR}${REMAINING} requests left${RESET} ${DIM}(UTC daily quota)${RESET}"
  else
    printf '%s\n' "OpenRouter FREE · ${MODEL}"
    printf '%s\n' "Quota data unavailable — run claude-usage in Terminal"
  fi
else
  printf '%s\n' "OpenRouter FREE · ${MODEL}"
  printf '%s\n' "Quota data unavailable — check Keychain / network"
fi
