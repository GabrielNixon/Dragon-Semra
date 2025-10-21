"""Synonym enrichment utilities."""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from dragon_semra.semra.artifacts import Artifact, ProvenanceRecord


class SynonymEnricher:
    """Apply configured synonym lexicons to artifacts."""

    def __init__(
        self,
        lexicon: Dict[str, Sequence[str]],
        *,
        similarity_threshold: float,
    ) -> None:
        self.lexicon = {key.lower(): tuple(values) for key, values in lexicon.items()}
        self.similarity_threshold = similarity_threshold

    def enrich(self, artifacts: Iterable[Artifact]) -> List[Artifact]:
        enriched = []
        for artifact in artifacts:
            new_synonyms = self._match_synonyms(artifact.name, artifact.attributes)
            if new_synonyms:
                artifact.synonyms.extend(sorted(new_synonyms - set(artifact.synonyms)))
                artifact.provenance.append(
                    ProvenanceRecord(
                        source="synonym-enricher",
                        recorded_at=_now_utc(),
                        note=f"Added {len(new_synonyms)} synonyms",
                    )
                )
            enriched.append(artifact)
        return enriched

    def _match_synonyms(self, name: str, attributes: Dict[str, str]) -> set[str]:
        candidates = set()
        search_terms = {name.lower(), *(value.lower() for value in attributes.values())}
        for term in search_terms:
            for key, synonyms in self.lexicon.items():
                score = _normalized_similarity(term, key)
                if score >= self.similarity_threshold:
                    candidates.update(synonyms)
        return candidates


def _normalized_similarity(left: str, right: str) -> float:
    """Return a simple normalized similarity ratio between two strings."""

    left = left.strip().lower()
    right = right.strip().lower()
    if not left or not right:
        return 0.0

    overlap = len(set(left.split()) & set(right.split()))
    union = len(set(left.split()) | set(right.split()))
    if union == 0:
        return 0.0
    return overlap / union


def _now_utc():
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc)


__all__ = ["SynonymEnricher"]
