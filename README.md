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
  ingest/             - Source loaders (CSV and OWL ingestion)
  enrichment/         - Synonym, acronym, and optional LLM enrichers
  validation/         - Semra-inspired validation checks
  export/             - Artifact serialization utilities
  semra/              - Minimal Semra artifact data classes
config/
  sample_pipeline.yaml - Example pipeline configuration referencing sample data
  ontology_pipeline.yaml - Example OWL-based configuration for dropped ontologies
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

Refer to `config/sample_pipeline.yaml` for a CSV example and
`config/ontology_pipeline.yaml` for an OWL-focused configuration.

## Working with OWL ontologies

To exercise the ontology loader, download the `mp.owl` and `hp.owl` releases
and drop them into the repository's `data/` directory. The
`config/ontology_pipeline.yaml` file is preconfigured to ingest both files,
generate Semra-style artifacts with subclass relationships, and export the
combined result. Run it with:

```bash
python -m dragon_semra.cli config/ontology_pipeline.yaml
```

Depending on ontology size the run can take a few minutes; progress is logged
to standard output.

## Using an LLM for synonym expansion

The synonym enricher can fall back to an LLM when the configured lexicon does
not produce a match. Supply an OpenAI-compatible key via the
`DRAGON_SEMRA_LLM_KEY` environment variable and enable the `synonyms.llm`
section in your configuration (see the OWL sample). The pipeline will request a
comma-separated synonym list using the specified model. If the key is not
configured, the pipeline logs a warning and continues without LLM assistance.
