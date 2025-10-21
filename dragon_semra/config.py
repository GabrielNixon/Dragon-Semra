"""Configuration utilities for the Dragon-Semra pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml


@dataclass
class SourceConfig:
    """Configuration describing a single ingestion source."""

    path: Path
    format: str = "csv"
    field_mapping: Dict[str, str] = field(default_factory=dict)
    id_field: str = "id"
    type_field: str = "type"
    name_field: str = "name"
    description_field: Optional[str] = None


@dataclass
class SynonymConfig:
    """Configuration for synonym enrichment."""

    lexicon: Dict[str, Iterable[str]] = field(default_factory=dict)
    similarity_threshold: float = 0.75


@dataclass
class AcronymConfig:
    """Configuration for acronym enrichment."""

    lexicon: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExportConfig:
    """Configuration for export stage."""

    directory: Path
    format: str = "json"


@dataclass
class PipelineConfig:
    """Top-level pipeline configuration."""

    sources: List[SourceConfig]
    synonyms: SynonymConfig = field(default_factory=SynonymConfig)
    acronyms: AcronymConfig = field(default_factory=AcronymConfig)
    export: ExportConfig = field(default_factory=lambda: ExportConfig(directory=Path("./artifacts")))


def _parse_source_config(raw: Dict) -> SourceConfig:
    return SourceConfig(
        path=Path(raw["path"]),
        format=raw.get("format", "csv"),
        field_mapping=raw.get("field_mapping", {}),
        id_field=raw.get("id_field", "id"),
        type_field=raw.get("type_field", "type"),
        name_field=raw.get("name_field", "name"),
        description_field=raw.get("description_field"),
    )


def _parse_synonym_config(raw: Dict) -> SynonymConfig:
    return SynonymConfig(
        lexicon={k: tuple(v) for k, v in raw.get("lexicon", {}).items()},
        similarity_threshold=float(raw.get("similarity_threshold", 0.75)),
    )


def _parse_acronym_config(raw: Dict) -> AcronymConfig:
    return AcronymConfig(lexicon=raw.get("lexicon", {}))


def _parse_export_config(raw: Dict) -> ExportConfig:
    directory = Path(raw.get("directory", "./artifacts"))
    return ExportConfig(directory=directory, format=raw.get("format", "json"))


def load_config(path: Path | str) -> PipelineConfig:
    """Load a :class:`PipelineConfig` from a YAML file."""

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    sources = [_parse_source_config(entry) for entry in raw.get("sources", [])]
    if not sources:
        raise ValueError("Pipeline configuration must define at least one source")

    synonyms = _parse_synonym_config(raw.get("synonyms", {}))
    acronyms = _parse_acronym_config(raw.get("acronyms", {}))
    export = _parse_export_config(raw.get("export", {}))

    return PipelineConfig(sources=sources, synonyms=synonyms, acronyms=acronyms, export=export)


__all__ = [
    "SourceConfig",
    "SynonymConfig",
    "AcronymConfig",
    "ExportConfig",
    "PipelineConfig",
    "load_config",
]
