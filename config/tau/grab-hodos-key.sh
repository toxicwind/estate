#!/usr/bin/env bash
set -uo pipefail
OUT=~/.tau/hodos.key
CONSOLE='https://awrawr-pc:25212'
CURL=(curl -sk -m 5)
: > "$OUT.tmp"
log() { printf '%s\n' "$*" >&2; }

# 1) env
for v in HODOS_API_KEY HODOS_KEY HODOS_TOKEN API_KEY; do
  [[ -n "${!v:-}" ]] && { log "found \$$v"; printf '%s' "${!v}" > "$OUT.tmp"; break; }
done

# 2) known config files
if [[ ! -s "$OUT.tmp" ]]; then
  for f in ~/.tau/hodos.yml ~/.config/hodos/config.yml ~/.config/hodos/config.json \
           /home/toxic/projects/hodos/.env /home/toxic/projects/hodos/.env.local \
           /home/toxic/projects/hodos/config.yml /home/toxic/projects/hodos/config.toml; do
    [[ -f "$f" ]] || continue
    k=$(grep -aoE '(api[_-]?key|token|secret)["'\'']?\s*[:=]\s*["'\'']?[A-Za-z0-9._\-]{16,}' "$f" 2>/dev/null \
        | head -1 | grep -aoE '[A-Za-z0-9._\-]{16,}$')
    [[ -n "$k" ]] && { log "found in $f"; printf '%s' "$k" > "$OUT.tmp"; break; }
  done
fi

# 3) console API endpoints
if [[ ! -s "$OUT.tmp" ]]; then
  for ep in /api/key /api/keys /api/token /api/config /api/settings \
            /api/v1/key /api/v1/keys /api/v1/config /api/v1/settings \
            /api/auth/key /api/auth/keys /api/hodos/key /api/proxy/key \
            /api/admin/key /api/admin/config /api/console/key \
            /key /keys /token /config.json /settings.json /api/config.json; do
    body=$("${CURL[@]}" "$CONSOLE$ep" 2>/dev/null || true)
    [[ -z "$body" ]] && continue
    k=$(jq -r '
      (.key // .api_key // .apiKey // .token // .proxy_key // .hodos_key //
       .keys[0] // .keys[0].key // .keys[0].token //
       .data.key // .data.api_key // .data.apiKey // .data.token //
       .result.key // .result.token // empty)
    ' <<<"$body" 2>/dev/null || true)
    [[ -z "$k" || "$k" == "null" ]] && k=$(grep -aoE 'eyJ[A-Za-z0-9._\-]{30,}|sk-[A-Za-z0-9._\-]{20,}|[a-f0-9]{32,}|[A-Za-z0-9._\-]{32,}' <<<"$body" | head -1)
    [[ -n "$k" && ${#k} -ge 16 ]] && { log "found at $ep"; printf '%s' "$k" > "$OUT.tmp"; break; }
  done
fi

# 4) console HTML + JS bundles
if [[ ! -s "$OUT.tmp" ]]; then
  html=$("${CURL[@]}" "$CONSOLE/" 2>/dev/null || true)
  if [[ -n "$html" ]]; then
    k=$(grep -aoE '(api[_-]?key|token|secret)["'\'']?\s*[:=]\s*["'\'']?[A-Za-z0-9._\-]{20,}' <<<"$html" | head -1 | grep -aoE '[A-Za-z0-9._\-]{20,}$')
    [[ -z "$k" ]] && k=$(grep -aoE 'eyJ[A-Za-z0-9._\-]{30,}|sk-[A-Za-z0-9._\-]{20,}|[a-f0-9]{32,}' <<<"$html" | head -1)
    [[ -n "$k" ]] && { log "found in console HTML"; printf '%s' "$k" > "$OUT.tmp"; }
    if [[ ! -s "$OUT.tmp" ]]; then
      while IFS= read -r src; do
        [[ -z "$src" ]] && continue
        [[ "$src" == /* ]] && url="$CONSOLE$src" || url="$src"
        js=$("${CURL[@]}" "$url" 2>/dev/null || true)
        k=$(grep -aoE '(api[_-]?key|token|secret)["'\'']?\s*[:=]\s*["'\'']?[A-Za-z0-9._\-]{20,}' <<<"$js" | head -1 | grep -aoE '[A-Za-z0-9._\-]{20,}$')
        [[ -z "$k" ]] && k=$(grep -aoE 'eyJ[A-Za-z0-9._\-]{30,}|sk-[A-Za-z0-9._\-]{20,}|[a-f0-9]{32,}' <<<"$js" | head -1)
        [[ -n "$k" ]] && { log "found in $url"; printf '%s' "$k" > "$OUT.tmp"; break; }
      done < <(grep -aoE 'src="[^"]+\.js[^"]*"' <<<"$html" | cut -d'"' -f2)
    fi
  fi
fi

# 5) grep hodos project dir
if [[ ! -s "$OUT.tmp" && -d /home/toxic/projects/hodos ]]; then
  k=$(grep -raoE --include='*.yml' --include='*.yaml' --include='*.json' --include='*.env' --include='*.toml' \
      '(api[_-]?key|token|secret)["'\'']?\s*[:=]\s*["'\'']?[A-Za-z0-9._\-]{24,}' \
      /home/toxic/projects/hodos 2>/dev/null | head -1 | grep -aoE '[A-Za-z0-9._\-]{24,}$')
  [[ -n "$k" ]] && { log "found in hodos project"; printf '%s' "$k" > "$OUT.tmp"; }
fi

# 6) llama-swap default key probe
if [[ ! -s "$OUT.tmp" ]]; then
  for guess in 'llama-swap-local-key' 'sk-local' 'local' 'hodos' 'toxicwind' 'changeme' 'dev' 'test' 'admin' 'password'; do
    code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $guess" http://127.0.0.1:25193/v1/models)
    [[ "$code" == 200 ]] && { log "default key works: $guess"; printf '%s' "$guess" > "$OUT.tmp"; break; }
  done
fi

if [[ -s "$OUT.tmp" ]]; then
  mv "$OUT.tmp" "$OUT"; chmod 600 "$OUT"
  log "wrote $OUT ($(wc -c <"$OUT") bytes)"
  code=$("${CURL[@]}" -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $(<"$OUT")" http://127.0.0.1:25193/v1/models)
  log "verify /v1/models -> HTTP $code"
  [[ "$code" == 200 ]] && exit 0
  log "key found but 401 — wrong key"; exit 2
fi
log "AUTO-GRAB FAILED. Open $CONSOLE F12->Network->copy Authorization header"
exit 1
