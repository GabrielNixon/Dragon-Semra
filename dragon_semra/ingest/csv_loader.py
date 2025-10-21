"""CSV ingestion routines."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable

from dragon_semra.semra.artifacts import Artifact, ProvenanceRecord
from .base import Ingestor


class CsvIngestor(Ingestor):
    """Load artifacts from CSV files using a field mapping."""

    def __init__(
        self,
        path: Path,
        field_mapping: Dict[str, str],
        *,
        id_field: str,
        type_field: str,
        name_field: str,
        description_field: str | None = None,
    ) -> None:
        super().__init__(path)
        self.field_mapping = field_mapping
        self.id_field = id_field
        self.type_field = type_field
        self.name_field = name_field
        self.description_field = description_field

    def load(self) -> Iterable[Artifact]:
        with self.path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield self._row_to_artifact(row)

    def _row_to_artifact(self, row: Dict[str, str]) -> Artifact:
        identifier = row[self.field_mapping.get("id", self.id_field)]
        artifact_type = row[self.field_mapping.get("type", self.type_field)]
        name = row[self.field_mapping.get("name", self.name_field)]
        description = None
        if self.description_field:
            description = row.get(self.field_mapping.get("description", self.description_field))

        attributes = {
            target: row[source]
            for source, target in self.field_mapping.items()
            if source not in {"id", "name", "type", "description"}
        }

        provenance = [
            ProvenanceRecord(source=str(self.path), recorded_at=_now_utc(), note="Ingested from CSV")
        ]

        return Artifact(
            identifier=identifier,
            artifact_type=artifact_type,
            name=name,
            description=description,
            attributes=attributes,
            provenance=provenance,
        )


def _now_utc():
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc)


__all__ = ["CsvIngestor"]
