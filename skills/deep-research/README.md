# deep-research

[![CI](https://github.com/toxic/estate/skills/deep-research/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A deep research platform for exploring, analyzing, and synthesizing academic and industry research. Provides advanced querying, visualization, and citation management for scholarly work.

## Hero

Conduct rigorous research at scale — discover papers, analyze trends, and build comprehensive literature reviews with deep analytical capabilities.

## Features

- **Advanced Search** — multi-field indexing with fuzzy matching and Boolean operators
- **Citation Graph** — visualize and navigate relationships between papers
- **Trend Analysis** — detect emerging topics and research trajectories
- **Full-Text Retrieval** — search and retrieve from millions of documents
- **Collaborative Workspaces** — share research notebooks and annotations

## Quick Start

```bash
# Install deep-research
pip install deep-research

# Initialize a new research project
deep-research init --topic "large language models" --domain "AI/ML"

# Run a literature survey
deep-research survey --topic "LLMs" --depth 5

# Explore citation network
deep-research graph --paper "attention is all you need" --visualize
```

## Architecture

Deep-research employs a distributed architecture:

- **Index Cluster** — distributed search and retrieval engine
- **Analysis Engine** — performs NLP, statistical, and network analysis
- **Visualization Layer** — interactive charts and network graphs
- **Collaboration Server** — real-time sharing and annotation

Key components:
- **Paper Indexer** — ingests and indexes academic papers
- **Semantic Analyzer** — understands context and relationships
- **Trend Detector** — identifies rising and falling research areas
- **Citation Linker** — maps influence networks across publications

## Configuration

Primary configuration: `config/research.yaml`

Key sections:

- `databases` — sources of research data (arXiv, PubMed, IEEE)
- `search_params` — query strings, filters, and ranking algorithms
- `visualizations` — chart types and layout preferences
- `collab` — collaboration settings and permissions

Example configuration:

```yaml
databases:
  arxiv: "https://export.arxiv.org/api/query?search_query=all&sort_by=submitted_date_desc"
  pubmed: "https://pubmed.ncbi.nlm.nih.gov/search"

search_params:
  query: "transformers efficiency"
  language: "en"
  min_papers: 10
  max_depth: 5

visualizations:
  trend_chart: true
  citation_network: true
  wordcloud: true

collab:
  enabled: true
  max_users: 50
  permissions: ["read", "comment"]
```

## Optional Services

- **API** — programmatic access to search and analysis features
- **Notebook Support** — Jupyter integration for interactive research
- **Team Workspaces** — shared research environments with version control

## Development

```bash
# Clone the repository
git clone https://github.com/toxic/estate/skills/deep-research
cd deep-research

# Install dependencies
pip install -e .

# Run the test suite
pytest

# Initialize a new research project
deep-research init --help
```

## License

MIT License.

## Security

- All research data is encrypted at rest
- Access to sensitive papers is controlled by authentication
- Audit logs track all research activities
- Regular security scans integrated into CI
