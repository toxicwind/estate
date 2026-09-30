#!/bin/bash
set -u
curl -s -m 10 http://127.0.0.1:25135/squawk-feed/ui -o /tmp/feedui.html
T=$(grep -o "token *= *'[^']*'" /tmp/feedui.html | head -1 | sed "s/.*'//;s/'$//")
if [ -z "$T" ]; then echo "NO_EMBEDDED_TOKEN_FOUND"; exit 1; fi
printf 'embedded token sha16: '
printf '%s' "$T" | sha256sum | cut -c1-16
curl -s -m 15 -o /tmp/wait.json -w 'wait http=%{http_code} bytes=%{size_download}\n' -H "Authorization: Bearer $T" 'http://127.0.0.1:25135/squawk-feed/wait?since=0&channel=fleet'
head -c 200 /tmp/wait.json; echo
