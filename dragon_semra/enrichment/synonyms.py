"""Synonym enrichment utilities."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Sequence, Set

from dragon_semra.semra.artifacts import Artifact, ProvenanceRecord

from .llm import LLMSynonymClient

LOGGER = logging.getLogger(__name__)


class SynonymEnricher:
    """Apply configured synonym lexicons to artifacts."""

    def __init__(
        self,
        lexicon: Dict[str, Sequence[str]],
        *,
        similarity_threshold: float,
        llm_client: LLMSynonymClient | None = None,
        llm_context_fields: Sequence[str] = (),
    ) -> None:
        self.lexicon = {key.lower(): tuple(values) for key, values in lexicon.items()}
        self.similarity_threshold = similarity_threshold
        self.llm_client = llm_client
        self.llm_context_fields = tuple(llm_context_fields)
        self._llm_cache: Dict[str, List[str]] = {}

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

    def _match_synonyms(self, name: str, attributes: Dict[str, str]) -> Set[str]:
        candidates: Set[str] = set()
        search_terms = {name.lower(), *(value.lower() for value in attributes.values())}
        for term in search_terms:
            for key, synonyms in self.lexicon.items():
                score = _normalized_similarity(term, key)
                if score >= self.similarity_threshold:
                    candidates.update(synonyms)

        if not candidates and self.llm_client:
            candidates.update(self._generate_with_llm(name, attributes))

        return candidates

    def _generate_with_llm(self, name: str, attributes: Dict[str, str]) -> Set[str]:
        if name in self._llm_cache:
            return set(self._llm_cache[name])

        context_lines = []
        for field in self.llm_context_fields:
            value = attributes.get(field)
            if value:
                context_lines.append(f"{field}: {value}")
        context = "\n".join(context_lines) if context_lines else None

        try:
            suggestions = self.llm_client.generate_synonyms(name, context=context)
        except Exception as exc:  # pragma: no cover - depends on network
            LOGGER.warning("LLM synonym generation failed for '%s': %s", name, exc)
            self._llm_cache[name] = []
            return set()

        normalized = sorted({value.strip() for value in suggestions if value.strip()})
        self._llm_cache[name] = normalized
        return set(normalized)


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
