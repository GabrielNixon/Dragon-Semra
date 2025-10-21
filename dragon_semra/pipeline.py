"""End-to-end enrichment pipeline orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from dragon_semra.config import PipelineConfig, load_config
from dragon_semra.enrichment import AcronymEnricher, SynonymEnricher
from dragon_semra.export.writer import ArtifactWriter
from dragon_semra.ingest.csv_loader import CsvIngestor
from dragon_semra.semra.artifacts import Artifact
from dragon_semra.validation.schema import validate_artifacts


class EnrichmentPipeline:
    """Coordinate ingestion, enrichment, validation, and export."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def run(self) -> List[Artifact]:
        artifacts = self._ingest()
        artifacts = self._enrich(artifacts)
        self._validate(artifacts)
        self._export(artifacts)
        return artifacts

    def _ingest(self) -> List[Artifact]:
        artifacts: List[Artifact] = []
        for source in self.config.sources:
            if source.format.lower() != "csv":
                raise ValueError(f"Unsupported source format: {source.format}")
            ingestor = CsvIngestor(
                source.path,
                source.field_mapping,
                id_field=source.id_field,
                type_field=source.type_field,
                name_field=source.name_field,
                description_field=source.description_field,
            )
            artifacts.extend(list(ingestor.load()))
        return artifacts

    def _enrich(self, artifacts: Iterable[Artifact]) -> List[Artifact]:
        artifacts = list(artifacts)
        synonym_enricher = SynonymEnricher(
            lexicon=self.config.synonyms.lexicon,
            similarity_threshold=self.config.synonyms.similarity_threshold,
        )
        artifacts = synonym_enricher.enrich(artifacts)
        acronym_enricher = AcronymEnricher(self.config.acronyms.lexicon)
        return acronym_enricher.enrich(artifacts)

    def _validate(self, artifacts: Iterable[Artifact]) -> None:
        issues = validate_artifacts(artifacts)
        if issues:
            issue_text = "\n".join(issues)
            raise ValueError(f"Artifact validation failed:\n{issue_text}")

    def _export(self, artifacts: Iterable[Artifact]) -> None:
        writer = ArtifactWriter(self.config.export.directory, format=self.config.export.format)
        writer.write(artifacts)


def run_from_config(path: Path | str) -> List[Artifact]:
    config = load_config(path)
    pipeline = EnrichmentPipeline(config)
    return pipeline.run()


__all__ = ["EnrichmentPipeline", "run_from_config"]
