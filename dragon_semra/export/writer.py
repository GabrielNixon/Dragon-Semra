"""Export enriched artifacts to disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from dragon_semra.semra.artifacts import Artifact


class ArtifactWriter:
    """Persist artifacts to a directory."""

    def __init__(self, directory: Path, *, format: str = "json") -> None:
        self.directory = Path(directory)
        self.format = format
        self.directory.mkdir(parents=True, exist_ok=True)

    def write(self, artifacts: Iterable[Artifact]) -> None:
        if self.format != "json":
            raise ValueError(f"Unsupported export format: {self.format}")

        for artifact in artifacts:
            path = self.directory / f"{artifact.identifier}.json"
            with path.open("w", encoding="utf-8") as handle:
                json.dump(_artifact_to_dict(artifact), handle, indent=2, default=str)


def _artifact_to_dict(artifact: Artifact) -> dict:
    return {
        "identifier": artifact.identifier,
        "artifact_type": artifact.artifact_type,
        "name": artifact.name,
        "description": artifact.description,
        "attributes": artifact.attributes,
        "synonyms": artifact.synonyms,
        "acronyms": artifact.acronyms,
        "relationships": [
            {
                "predicate": rel.predicate,
                "target_id": rel.target_id,
                "confidence": rel.confidence,
                "provenance": [
                    {
                        "source": prov.source,
                        "recorded_at": prov.recorded_at.isoformat(),
                        "note": prov.note,
                    }
                    for prov in rel.provenance
                ],
            }
            for rel in artifact.relationships
        ],
        "provenance": [
            {
                "source": prov.source,
                "recorded_at": prov.recorded_at.isoformat(),
                "note": prov.note,
            }
            for prov in artifact.provenance
        ],
    }


__all__ = ["ArtifactWriter"]
