#!/bin/bash
# readme-op audit v2: latest README.md-touching commit per toxicwind repo
IN=/home/toxic/.fleet-bus/readme-op-repos.tsv
OUT=/home/toxic/.fleet-bus/readme-op-audit.tsv
: > "$OUT"
while IFS=$'\t' read -r name branch pushed fork archived; do
  [ -z "$name" ] && continue
  line=$(gh api "repos/toxicwind/${name}/commits?path=README.md&per_page=1" --jq '[.[0].sha[0:7], .[0].commit.author.date, (.[0].commit.message | split("\n")[0] | .[0:120])] | @tsv' 2>/dev/null)
  printf '%s\t%s\t%s\n' "$name" "$branch" "$line" >> "$OUT"
done < "$IN"
echo "AUDIT DONE: $(wc -l < "$OUT") repos"
