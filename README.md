# Dragon-Semra Enrichment Pipeline

This repository provides a lightweight data-enrichment pipeline inspired by the
[Dragon AI cookiecutter template](https://github.com/monarch-initiative/dragon-ai-cookiecutter)
and the [Semra artifact structure](https://semra.readthedocs.io/en/stable/artifacts.html).
It demonstrates how to normalize raw tabular inputs, attach synonyms and
acronyms, validate Semra-style artifacts, and persist the results.

## Repository Layout

```
dragon_semra/
  cli.py              - Command-line interface wrapper
  config.py           - YAML-based pipeline configuration parsing
  pipeline.py         - Ingestion, enrichment, validation, and export orchestration
  ingest/             - Source loaders (CSV provided, easily extensible)
  enrichment/         - Synonym and acronym enrichers
  validation/         - Semra-inspired validation checks
  export/             - Artifact serialization utilities
  semra/              - Minimal Semra artifact data classes
config/
  sample_pipeline.yaml - Example pipeline configuration referencing sample data
data/
  sample_input.csv     - Example CSV demonstrating the expected schema
```

## Getting Started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. **Run the sample pipeline**

   ```bash
   python -m dragon_semra.cli config/sample_pipeline.yaml
   ```

   Successful execution writes enriched artifact JSON files to the `artifacts/`
   directory.

## Configuration Overview

The pipeline is configured via YAML. Each entry in `sources` defines a data
source with field mappings that normalize the raw columns into the Semra-style
artifact schema. Synonym and acronym enrichers use configurable lexicons to
append additional metadata while recording provenance entries. The export block
controls the output directory and format.

Refer to `config/sample_pipeline.yaml` for a complete working example.
