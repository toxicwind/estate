#!/bin/bash
# config-cartographer: daemon-section diff vs canonical
CANON=/home/toxic/sovereign/pitchfork.toml
grep -F '[daemons."' "$CANON" | grep -oE 'daemons\."[^"]+"' | sed 's/daemons\.//' | tr -d '"' | sort -u > /tmp/d.canon
echo "canonical daemon count: $(wc -l < /tmp/d.canon)"
echo
while IFS= read -r f; do
  h=$(sha256sum "$f" | cut -c1-12)
  [ "$h" = "$(sha256sum "$CANON" | cut -c1-12)" ] && continue
  grep -F '[daemons."' "$f" 2>/dev/null | grep -oE 'daemons\."[^"]+"' | sed 's/daemons\.//' | tr -d '"' | sort -u > /tmp/d.other
  n=$(wc -l < /tmp/d.other)
  echo "== $f ($n daemons)"
  echo "  +in this, not in canon: $(comm -13 /tmp/d.canon /tmp/d.other | tr '\n' ' ' | head -c 400)"
  echo "  -missing from this: $(comm -23 /tmp/d.canon /tmp/d.other | wc -l) daemon(s)"
done < <(find /home/toxic -name 'pitchfork.toml' -not -path '*/node_modules/*' -not -path '*/.git/*' ! -type l 2>/dev/null)
