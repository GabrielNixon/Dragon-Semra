"""End-to-end enrichment pipeline orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from dragon_semra.config import PipelineConfig, load_config
from dragon_semra.enrichment import AcronymEnricher, SynonymEnricher
from dragon_semra.enrichment.llm import LLMConfigurationError, LLMSynonymClient
from dragon_semra.export.writer import ArtifactWriter
from dragon_semra.ingest import OwlIngestor, OwlIngestorSettings
from dragon_semra.ingest.csv_loader import CsvIngestor
from dragon_semra.semra.artifacts import Artifact
from dragon_semra.validation.schema import validate_artifacts

LOGGER = logging.getLogger(__name__)


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
            format_name = source.format.lower()
            if format_name == "csv":
                ingestor = CsvIngestor(
                    source.path,
                    source.field_mapping,
                    id_field=source.id_field,
                    type_field=source.type_field,
                    name_field=source.name_field,
                    description_field=source.description_field,
                )
            elif format_name == "owl":
                settings = OwlIngestorSettings(
                    artifact_type=str(source.parameters.get("artifact_type", "ontology_class")),
                    label_predicates=_coerce_predicates(
                        source.parameters.get("label_predicates"),
                        OwlIngestorSettings.label_predicates,
                    ),
                    synonym_predicates=_coerce_predicates(
                        source.parameters.get("synonym_predicates"),
                        OwlIngestorSettings.synonym_predicates,
                    ),
                    definition_predicates=_coerce_predicates(
                        source.parameters.get("definition_predicates"),
                        OwlIngestorSettings.definition_predicates,
                    ),
                    namespace_predicates=_coerce_predicates(
                        source.parameters.get("namespace_predicates"),
                        OwlIngestorSettings.namespace_predicates,
                    ),
                    relationship_predicates=_coerce_predicates(
                        source.parameters.get("relationship_predicates"),
                        OwlIngestorSettings.relationship_predicates,
                    ),
                )
                ingestor = OwlIngestor(source.path, settings=settings)
            else:
                raise ValueError(f"Unsupported source format: {source.format}")
            artifacts.extend(list(ingestor.load()))
        return artifacts

    def _enrich(self, artifacts: Iterable[Artifact]) -> List[Artifact]:
        artifacts = list(artifacts)
        llm_client = None
        llm_context_fields = ()
        if self.config.synonyms.llm and self.config.synonyms.llm.enabled:
            try:
                llm_client = LLMSynonymClient(
                    provider=self.config.synonyms.llm.provider,
                    model=self.config.synonyms.llm.model,
                    max_synonyms=self.config.synonyms.llm.max_synonyms,
                    prompt_template=self.config.synonyms.llm.prompt_template,
                    system_prompt=self.config.synonyms.llm.system_prompt,
                )
                llm_context_fields = tuple(self.config.synonyms.llm.context_fields)
            except LLMConfigurationError as exc:
                LOGGER.warning("LLM synonym generation disabled: %s", exc)

        synonym_enricher = SynonymEnricher(
            lexicon=self.config.synonyms.lexicon,
            similarity_threshold=self.config.synonyms.similarity_threshold,
            llm_client=llm_client,
            llm_context_fields=llm_context_fields,
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


def _coerce_predicates(value, default) -> tuple[str, ...]:
    if value is None:
        return tuple(default)
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value)
    return (str(value),)
