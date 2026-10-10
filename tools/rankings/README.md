# rankings

First-class rankings frontend for the estate.

Lives next to tools/bench-radar. Not nested under roundup.

## What it does

- Rankings page loads public/benchmarks.json (generated from latest estate sweep ranking)
- Radar page documents bench-radar (:25181) regression alerts

## Run

cd /home/toxic/estate/tools/rankings
npm install
npm run dev

Generate data with the script in ranch/roundup/scripts/gen-benchmarks-json.ts (update output path if needed).

## Design

Follows open-design/frontend-design skill: subject is model ranking (quality desc, p50 asc). Keep visual identity tied to that.
