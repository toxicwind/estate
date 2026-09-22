from pathlib import Path
p = Path("/home/toxic/.worktrees/vex-html/docs/fleet-knowledgebase.md")
lines = p.read_text().split("\n")
row = ("| vex-html-cors | Squawk HTML-first-class + CORS (Chris direct order "
       "2026-09-21): raw HTML/CSS renders as authored in ui.html (renderer "
       "passes tags, inline styles, <style>/<script> blocks through; fenced "
       "code stays literal), CORS on feed :25135 (OPTIONS preflight 204 + "
       "ACAO on JSON/UI/404); tests html_body_served_verbatim + "
       "cors_preflight_and_headers; renderer 19/19 node checks; live POST "
       "round-trip byte-identical | Vex (Ember's crew) | RUNNING |")
assert lines[193].startswith("| taps-nats |"), lines[193][:40]
lines.insert(194, row)
p.write_text("\n".join(lines))
print("KB row added")
