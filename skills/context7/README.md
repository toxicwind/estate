# context7

[![CI](https://github.com/toxic/estate/skills/context7/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A contextual documentation lookup system that resolves library names to Context7 library IDs and fetches related documentation. Provides instant, accurate references for developers working across large codebases.

## Hero

Get precise, up-to-date documentation links for any library or concept with zero manual searching.

## Features

- **Library Resolution** — maps human-friendly names to Context7 library IDs
- **Context-Aware Lookup** — retrieves relevant docs based on surrounding code
- **Real-time Updates** — pulls latest documentation from external sources
- **Cross-reference Navigation** — jump between related concepts and files
- **Export Capabilities** — generate documentation indexes and links

## Quick Start

```bash
# Install context7
pip install context7

# Resolve a library name
context7 resolve "torchvision"

# Get documentation for a specific file
context7 doc "src/models/transformer.py"

# Search within a library
context7 search "transformers" --library torch
```

## Architecture

Context7 operates through three layers:

1. **Resolver** — queries external metadata stores (PyPI, GitHub, internal registries)
2. **Indexer** — builds inverted indices for fast lookup by name, category, and relationship
3. **Renderer** — presents formatted documentation with links and highlights

Key components:
- **Name Normalizer** — standardizes library names across ecosystems
- **Context Builder** — aggregates related documents based on code proximity
- **Link Validator** — ensures all references are valid and up-to-date

## Configuration

Primary configuration: `config/context7.yaml`

Key sections:

- `libraries` — pre-configured library mappings
- `indexes` — custom index definitions for domain-specific terms
- `sources` — external sources to query (GitHub, PyPI, internal)
- `outputs` — rendering preferences (HTML, Markdown, API docs)

Example configuration:

```yaml
libraries:
  pytorch: "https://pypi.org/project/pytorch/"
  transformers: "https://github.com/huggingface/transformers"

indexes:
  - name: "torch"
    source: "pypi"
    filters: ["torch", "tensorflow"]

sources:
  - name: "github"
    org: "microsoft"
    repos: ["starcoder/starcoder"]

outputs:
  format: "markdown"
  theme: "dark"
```

## Optional Services

- **Live Index** — continuously updates the index from external sources
- **API Client** — programmatically query Context7 for specific libraries
- **Integration** — connect to IDEs via language servers

## Development

```bash
# Setup development environment
pip install -e .

# Run the resolver tests
pytest tests/resolver/

# Generate an index
context7 index --output index.yaml
```

## License

MIT License.

## Security

- All external queries are rate-limited to prevent abuse
- Private library mappings are encrypted at rest
- Output links are validated before display
- Audit logs track all resolution queries
