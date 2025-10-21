"""Acronym enrichment utilities."""

from __future__ import annotations

from typing import Dict, Iterable, List

from dragon_semra.semra.artifacts import Artifact, ProvenanceRecord


class AcronymEnricher:
    """Populate acronym lists based on configured expansions."""

    def __init__(self, lexicon: Dict[str, str]) -> None:
        self.lexicon = {key.lower(): value for key, value in lexicon.items()}

    def enrich(self, artifacts: Iterable[Artifact]) -> List[Artifact]:
        enriched = []
        for artifact in artifacts:
            new_acronyms = self._match_acronyms(artifact.name, artifact.attributes)
            if new_acronyms:
                artifact.acronyms.extend(sorted(new_acronyms - set(artifact.acronyms)))
                artifact.provenance.append(
                    ProvenanceRecord(
                        source="acronym-enricher",
                        recorded_at=_now_utc(),
                        note=f"Added {len(new_acronyms)} acronyms",
                    )
                )
            enriched.append(artifact)
        return enriched

    def _match_acronyms(self, name: str, attributes: Dict[str, str]) -> set[str]:
        candidates = set()
        search_terms = {name.lower(), *(value.lower() for value in attributes.values())}
        for term in search_terms:
            for acronym, expansion in self.lexicon.items():
                if expansion.lower() == term:
                    candidates.add(acronym)
        return candidates


def _now_utc():
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc)


__all__ = ["AcronymEnricher"]
