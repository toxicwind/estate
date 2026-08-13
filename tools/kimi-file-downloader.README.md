# Kimi File Downloader

Fast concurrent file downloader for Kimi API/HAR archives.

## Usage

### 1. List-only mode (see what would be downloaded)
```bash
python3 kimi-file-downloader.py \
  --har "www.kimi.com_Archive [26-08-12 18-48-34].har.txt" \
  --list-only
```

### 2. Download everything from HAR only
```bash
python3 kimi-file-downloader.py \
  --har "www.kimi.com_Archive [26-08-12 18-48-34].har.txt" \
  --output ./kimi_files \
  --workers 8
```

### 3. HAR + live API (discover files not captured in HAR)
```bash
python3 kimi-file-downloader.py \
  --har "www.kimi.com_Archive [26-08-12 18-48-34].har.txt" \
  --api \
  --jwt "eyJhbGciOiJIUzUxMi..." \
  --output ./kimi_files \
  --workers 8
```

## Options

| Option | Description |
|--------|-------------|
| `--har` | Path to HAR archive file |
| `--jwt` | JWT token (defaults to built-in) |
| `--output` | Output directory (default: ./kimi_downloads) |
| `--api` | Also fetch from live API feeds |
| `--workers` | Concurrent downloads (default: 8) |
| `--list-only` | Only list URLs, don't download |

## Features

- **Concurrent downloads** with configurable workers
- **Checksum verification** (SHA256) - skips already-downloaded files
- **Resume support** - continues partial downloads
- **HAR parsing** - extracts signUrl/previewUrl from browser archives
- **API pagination** - fetches all feed pages automatically
- **Filename extraction** - parses clean names from URL query params
- **Duplicate handling** - appends checksum prefix for collisions

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)

## Notes

- The built-in JWT may expire. Use `--jwt` with a fresh token if needed.
- HAR files exported from browser dev tools work best.
- Files are saved with sanitized names (special chars replaced).