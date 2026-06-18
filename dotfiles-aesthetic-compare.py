#!/usr/bin/env python3
"""
SOVEREIGN DOTFILES AESTHETIC COMPARATOR
Forks JSON Crack-style viz + our best awk/grouping strategy
One script → beautiful interactive HTML dashboard
"""

import json
from collections import defaultdict
from pathlib import Path
import webbrowser
import sys

# ====================== CONFIG ======================
JSONL_PATH = Path.home() / "dotfiles_pull" / "dotfiles_env.jsonl"
OUTPUT_HTML = Path.home() / "dotfiles_pull" / "dotfiles-comparison.html"
# ====================================================

def load_and_clean(jsonl_path: Path):
    data = []
    with open(jsonl_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Clean variable names (fix the trailing = bug from awk)
                if obj.get("variable", "").endswith("="):
                    obj["variable"] = obj["variable"].rstrip("=")
                if obj.get("type") in ("export", "alias", "path") and obj.get("variable"):
                    data.append(obj)
            except json.JSONDecodeError:
                continue
    return data

def group_data(data):
    groups = defaultdict(list)
    for item in data:
        key = (item.get("type", ""), item.get("variable", ""))
        groups[key].append(item)

    results = []
    for (typ, var), items in groups.items():
        if not var:
            continue
        value_counts = defaultdict(list)
        for it in items:
            value_counts[it.get("value", "")].append(it.get("repo", ""))

        unique_values = []
        for val, repos in value_counts.items():
            unique_values.append({
                "value": val,
                "freq": len(repos),
                "repos": len(set(repos)),
                "sample_repos": list(set(repos))[:4]
            })

        unique_values.sort(key=lambda x: x["freq"], reverse=True)

        results.append({
            "type": typ,
            "variable": var,
            "count": len(items),
            "unique_values": unique_values,
            "conflict": len(unique_values) > 1
        })

    results.sort(key=lambda x: x["count"], reverse=True)
    return results

def generate_html(groups, total_lines):
    # Prepare data for JS
    exports = [g for g in groups if g["type"] == "export"][:25]
    aliases = [g for g in groups if g["type"] == "alias"][:25]
    conflicts = [g for g in groups if g["conflict"]][:30]
    consensus = []
    for g in groups:
        if g["unique_values"]:
            top = g["unique_values"][0]
            consensus.append({
                "var": g["variable"],
                "type": g["type"],
                "value": top["value"],
                "popularity": top["freq"]
            })
    consensus.sort(key=lambda x: x["popularity"], reverse=True)
    consensus = consensus[:25]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Dotfiles Aesthetic Comparator • Sovereign</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ background: #0a0a0a; color: #e5e5e5; }}
.card {{ background: #111; border: 1px solid #222; }}
table {{ border-collapse: collapse; }}
th, td {{ padding: 8px 12px; border-bottom: 1px solid #222; }}
.conflict {{ background: #3f1f1f; }}
</style>
</head>
<body class="p-8 max-w-7xl mx-auto">
<div class="flex justify-between items-center mb-8">
  <div>
    <h1 class="text-4xl font-bold tracking-tight">Dotfiles Aesthetic Comparator</h1>
    <p class="text-zinc-400">45 repos • {total_lines} lines analyzed</p>
  </div>
  <button onclick="window.location.reload()" 
          class="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">Refresh</button>
</div>

<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
  <div class="card p-6 rounded-2xl">
    <div class="text-sm text-zinc-400">Total Entries</div>
    <div class="text-5xl font-semibold mt-1">{total_lines}</div>
  </div>
  <div class="card p-6 rounded-2xl">
    <div class="text-sm text-zinc-400">Exports</div>
    <div class="text-5xl font-semibold mt-1">{len([g for g in groups if g['type']=='export'])}</div>
  </div>
  <div class="card p-6 rounded-2xl">
    <div class="text-sm text-zinc-400">Aliases</div>
    <div class="text-5xl font-semibold mt-1">{len([g for g in groups if g['type']=='alias'])}</div>
  </div>
  <div class="card p-6 rounded-2xl">
    <div class="text-sm text-zinc-400">Conflicts</div>
    <div class="text-5xl font-semibold mt-1 text-red-400">{len(conflicts)}</div>
  </div>
</div>

<!-- TABS -->
<div class="flex gap-2 mb-4 border-b border-zinc-800">
  <button onclick="showTab('exports')" class="tab-btn px-6 py-3 font-medium border-b-2 border-white" id="tab-exports">Exports</button>
  <button onclick="showTab('aliases')" class="tab-btn px-6 py-3 font-medium text-zinc-400 hover:text-white" id="tab-aliases">Aliases</button>
  <button onclick="showTab('conflicts')" class="tab-btn px-6 py-3 font-medium text-zinc-400 hover:text-white" id="tab-conflicts">Conflicts</button>
  <button onclick="showTab('consensus')" class="tab-btn px-6 py-3 font-medium text-zinc-400 hover:text-white" id="tab-consensus">Consensus</button>
</div>

<!-- EXPORTS TAB -->
<div id="exports" class="tab-content">
  <h2 class="text-2xl font-semibold mb-4">Top Exports</h2>
  <canvas id="exportsChart" class="mb-6"></canvas>
  <div class="overflow-auto max-h-[420px]">
    <table class="w-full text-sm">
      <thead><tr class="text-left text-zinc-400"><th>Variable</th><th>Count</th><th>Variants</th><th>Top Value</th></tr></thead>
      <tbody>
        {"".join(f'<tr><td class="font-mono">{g["variable"]}</td><td>{g["count"]}</td><td>{len(g["unique_values"])}</td><td class="font-mono text-emerald-400 truncate max-w-xs">{g["unique_values"][0]["value"] if g["unique_values"] else ""}</td></tr>' for g in exports)}
      </tbody>
    </table>
  </div>
</div>

<!-- ALIASES TAB -->
<div id="aliases" class="tab-content hidden">
  <h2 class="text-2xl font-semibold mb-4">Top Aliases</h2>
  <canvas id="aliasesChart" class="mb-6"></canvas>
  <div class="overflow-auto max-h-[420px]">
    <table class="w-full text-sm">
      <thead><tr class="text-left text-zinc-400"><th>Alias</th><th>Count</th><th>Variants</th><th>Top Value</th></tr></thead>
      <tbody>
        {"".join(f'<tr><td class="font-mono">{g["variable"]}</td><td>{g["count"]}</td><td>{len(g["unique_values"])}</td><td class="font-mono text-emerald-400 truncate max-w-xs">{g["unique_values"][0]["value"] if g["unique_values"] else ""}</td></tr>' for g in aliases)}
      </tbody>
    </table>
  </div>
</div>

<!-- CONFLICTS TAB -->
<div id="conflicts" class="tab-content hidden">
  <h2 class="text-2xl font-semibold mb-4 text-red-400">Variables with Multiple Values</h2>
  <div class="overflow-auto max-h-[520px]">
    <table class="w-full text-sm">
      <thead><tr class="text-left text-zinc-400"><th>Variable</th><th>Type</th><th>Variants</th><th>Top 2 Values</th></tr></thead>
      <tbody>
        {"".join(f'<tr class="conflict"><td class="font-mono">{g["variable"]}</td><td>{g["type"]}</td><td>{len(g["unique_values"])}</td><td class="font-mono text-xs">{g["unique_values"][0]["value"][:60]}<br>{g["unique_values"][1]["value"][:60] if len(g["unique_values"])>1 else ""}</td></tr>' for g in conflicts)}
      </tbody>
    </table>
  </div>
</div>

<!-- CONSENSUS TAB -->
<div id="consensus" class="tab-content hidden">
  <h2 class="text-2xl font-semibold mb-4">Consensus Recommendations (Most Popular Value)</h2>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
    {"".join(f'<div class="card p-4 rounded-xl"><div class="font-mono text-sm">{c["var"]}</div><div class="text-emerald-400 font-mono mt-1 break-all">{c["value"]}</div><div class="text-xs text-zinc-500 mt-1">{c["popularity"]} repos agree</div></div>' for c in consensus)}
  </div>
</div>

<script>
function showTab(tab) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('border-white', 'text-white'));
  document.getElementById(tab).classList.remove('hidden');
  document.getElementById('tab-' + tab).classList.add('border-white', 'text-white');
}}

// Charts
function createChart(id, labels, data, title) {{
  new Chart(document.getElementById(id), {{
    type: 'bar',
    data: {{ labels, datasets: [{{ label: title, data, backgroundColor: '#3b82f6' }}] }},
    options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color: '#888' }} }}, y: {{ ticks: {{ color: '#888' }} }} }} }}
  }});
}}

window.onload = function() {{
  // Exports chart
  const exportLabels = {json.dumps([g['variable'] for g in exports][:12])};
  const exportData = {json.dumps([g['count'] for g in exports][:12])};
  createChart('exportsChart', exportLabels, exportData, 'Occurrences');

  // Aliases chart
  const aliasLabels = {json.dumps([g['variable'] for g in aliases][:12])};
  const aliasData = {json.dumps([g['count'] for g in aliases][:12])};
  createChart('aliasesChart', aliasLabels, aliasData, 'Occurrences');

  // Default tab
  showTab('exports');
}};
</script>
</body>
</html>"""
    return html

def main():
    if not JSONL_PATH.exists():
        print(f"JSONL not found at {JSONL_PATH}")
        print("Run your fix.sh first.")
        sys.exit(1)

    print("Loading & cleaning data...")
    data = load_and_clean(JSONL_PATH)
    print(f"Loaded {len(data)} clean entries")

    print("Grouping...")
    groups = group_data(data)

    print("Generating beautiful HTML dashboard...")
    html = generate_html(groups, len(data))

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"Dashboard saved to: {OUTPUT_HTML}")

    try:
        webbrowser.open(f"file://{OUTPUT_HTML.absolute()}")
        print("Opened in your browser.")
    except:
        print("Open the file manually in your browser.")

if __name__ == "__main__":
    main()
