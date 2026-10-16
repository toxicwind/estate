#!/usr/bin/env bash
set -euo pipefail

# Scaffold a new Slidev deck following the skill conventions.
# Usage: scaffold.sh <project-name> [title] [author] [affiliation]

PROJECT=${1:-my-talk}
TITLE=${2:-Talk Title}
AUTHOR=${3:-Author Name}
AFFIL=${4:-Affiliation}

if [[ -e "$PROJECT" ]]; then
  echo "Error: '$PROJECT' already exists."
  exit 1
fi

mkdir -p "$PROJECT"/{images,assets,components,snippets}

cat > "$PROJECT/package.json" <<EOF
{
  "name": "$PROJECT",
  "type": "module",
  "private": true,
  "scripts": {
    "build": "slidev build",
    "dev": "slidev --open",
    "export": "slidev export"
  },
  "dependencies": {
    "@slidev/cli": "^0.51.0",
    "@slidev/theme-default": "^0.25.0",
    "slidev-theme-neversink": "^0.3.6",
    "slidev-theme-the-unnamed": "^0.0.22",
    "vue": "^3.5.0"
  }
}
EOF

cat > "$PROJECT/slides.md" <<EOF
---
theme: neversink
layout: cover
class: text-center
fonts:
  sans: Poppins
  mono: Source Code Pro
  weights: '200,400,600'
---

# $TITLE

**$AUTHOR**  
*$AFFIL*

<div class="absolute right-80px bottom-30px">
  <img src="/images/logo.png" width="240" />
</div>

---
EOF

cat > "$PROJECT/.gitignore" <<'EOF'
node_modules
.dist
dist
*.pdf
EOF

echo "Scaffolded '$PROJECT/'"
echo "Next: cd $PROJECT && npm install && npm run dev"
