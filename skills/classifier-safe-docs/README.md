# classifier-safe-docs

[![CI](https://github.com/toxic/estate/skills/classifier-safe-docs/actions/workflows/ci.yml/badge.svg)]
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]

A safety-focused documentation generator for classifier projects. Ensures all generated docs comply with safety guidelines, bias mitigation practices, and accessibility standards.

## Hero

Generate compliant, safe, and accessible documentation for your classifier models with built-in safety checks and bias detection.

## Features

- **Safety scanning** — detects potentially harmful content, PII, and unsafe recommendations
- **Bias detection** — identifies demographic and cultural biases in training data
- **Accessibility compliance** — ensures docs meet WCAG 2.1 standards
- **Automated formatting** — generates markdown, HTML, and API docs consistently
- **Versioned templates** — reusable doc structures for different classifier types

## Quick Start

```bash
# Install classifier-safe-docs
pip install classifier-safe-docs

# Generate docs for a trained model
classifier-safe-docs generate --model checkpoint.pkl --output docs/

# Validate safety
classifier-safe-docs validate --threshold 0.1
```

## Architecture

Classifier-safe-docs comprises four core modules:

1. **Content Analyzer** — scans text for safety violations and PII
2. **Bias Detector** — evaluates training data for representational bias
3. **Formatter** — converts analysis results into structured documentation
4. **Validator** — enforces accessibility and compliance rules

## Configuration

Key configuration areas:

- `safety_rules/` — defines prohibited content categories
- `bias_checks/` — bias detection heuristics and thresholds
- `accessibility/` — WCAG compliance checklists
- `templates/` — doc template variations for different model types

Example configuration:

```yaml
safety_rules:
  prohibited: ["hate speech", "violence", "sexual content"]
  pii_patterns: ["SSN", "email", "phone number"]

bias_checks:
  gender_bias: true
  racial_bias: true
  cultural_sensitivity: true

accessibility:
  contrast_ratio: 4.5
  alt_text_required: true
```

## Optional Services

- **CI Integration** — automated safety checks in the CI pipeline
- **Reporting** — generates compliance reports for audit trails
- **Dashboard** — visualizes safety metrics and bias scores

## Development

```bash
# Setup development environment
pip install -e .

# Run the documentation generator
python -m classifier_safe_docs generate --help

# Validate safety of a model
python -m classifier_safe_docs validate --model checkpoint.pkl
```

## License

MIT License.

## Security

- All generated docs are scanned for PII before publication
- Safety rules are configurable and auditable
- Dependency vulnerabilities are checked in CI
- Access to sensitive data is restricted to authorized users only
