# ml-serve — resident ML inference daemon

Hot-loaded ONNX segmentation + e621 native tag resolution over HTTP for the
desktop. No cold-start per call: the model loads lazily on first use and
stays resident; tag lookups are md5-cached.

There is deliberately **no local image tagger** — e621 already has maximal
tags, so redundant local compute is out. Tag resolution is
`md5(file) → e621 API → cached sidecar JSON`.

## Models (shared cache `~/.cache/quickshell/wallpaper-ml/`, never in git)

| endpoint | model | artifact |
|---|---|---|
| `POST /segment` | SkyTNT `anime-seg` ISNet (anime subject seg) | `isnetis.onnx` |

Execution providers: CUDA first (RTX 3090), CPU fallback. Load time and
rolling inference ms are exposed on `GET /health`.

## Endpoints

- `GET /health` → providers, models, e621 cache stats, timings
- `POST /lookup` `{"path": "/abs/img.png"}` → md5 + native e621
  `tag_string` (`null` + `"source": "miss"` when the file isn't on e621)
- `POST /segment` `{"path": "/abs/img.png"}` → subject bbox/centroid/coverage
  in original pixel coords (`bbox: null` when no subject)
- `POST /pick` `{"dir": "/abs/dir", "furry_boost": 3.0, "wm_penalty": 1.5,
  "target_aspect": 1.78}` → best pick by
  `aspect_term + upscale − boost·furry·male − penalty·watermark`,
  where furry/male/watermark are binary hits on native e621 tags
  (defaults: furry=`anthro kemono`, male=`male`, watermark=`watermark text`;
  override via `E621_TAGS_FURRY` / `E621_TAGS_MALE` / `E621_TAGS_WM`).
  Files missing from e621 score on geometry alone.

## Cache daemon

A background thread re-scans `ML_SERVE_POOL` (default
`~/Pictures/Wallpapers`) every `CACHE_INTERVAL_S` (default 60) and resolves
new/changed files against e621 into `.wallpaper-ml-cache.json` inside the
pool dir — entry schema
`{"mtime","size","w","h","md5","tag_string":[…]|null,"source","ms"}` —
so `/pick` is cache-hot. e621 lookups respect the 2 req/s limit (0.6s
spacing) and require no API key; a descriptive `User-Agent` is sent
(`E621_USER_AGENT`).

## Run it

```sh
python3 tools/ml-serve/server.py            # foreground, :25180
systemctl --user enable --now ml-serve      # durable (unit in systemd/)
```

Or via pitchfork: `[daemons.ml-serve]` stanza in `pitchfork.toml`
(`auto = ["start"]`).

## Bun client

`client/ml-serve-client.ts` — dependency-free (plain `fetch`), drop it
into any Bun tree. See `client/README.md`.
