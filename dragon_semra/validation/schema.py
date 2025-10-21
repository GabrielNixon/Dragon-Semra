"""Validation routines inspired by Semra constraints."""

from __future__ import annotations

from typing import Iterable, List

from dragon_semra.semra.artifacts import Artifact


class ValidationError(Exception):
    """Raised when validation of artifacts fails."""


def validate_artifacts(artifacts: Iterable[Artifact]) -> List[str]:
    """Validate artifacts and return a list of issues."""

    issues: List[str] = []
    seen_ids = set()
    for artifact in artifacts:
        if not artifact.identifier:
            issues.append("Artifact missing identifier")
        if artifact.identifier in seen_ids:
            issues.append(f"Duplicate artifact identifier: {artifact.identifier}")
        seen_ids.add(artifact.identifier)
        if not artifact.artifact_type:
            issues.append(f"Artifact {artifact.identifier} missing type")
        if not artifact.name:
            issues.append(f"Artifact {artifact.identifier} missing name")
    return issues


__all__ = ["ValidationError", "validate_artifacts"]
