"""OWL ingestion routines."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef

from dragon_semra.semra.artifacts import Artifact, ProvenanceRecord, Relationship

from .base import Ingestor

LOGGER = logging.getLogger(__name__)

OBO_IN_OWL = Namespace("http://www.geneontology.org/formats/oboInOwl#")
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")
OWL = Namespace("http://www.w3.org/2002/07/owl#")


@dataclass
class OwlIngestorSettings:
    """Runtime settings for :class:`OwlIngestor`."""

    artifact_type: str = "ontology_class"
    label_predicates: Sequence[str] = (str(RDFS.label),)
    synonym_predicates: Sequence[str] = (
        str(OBO_IN_OWL.hasExactSynonym),
        str(OBO_IN_OWL.hasRelatedSynonym),
        str(OBO_IN_OWL.hasNarrowSynonym),
        str(OBO_IN_OWL.hasBroadSynonym),
    )
    definition_predicates: Sequence[str] = (
        str(IAO["0000115"]),
        "http://purl.org/dc/terms/description",
    )
    namespace_predicates: Sequence[str] = (str(OBO_IN_OWL.hasOBONamespace),)
    relationship_predicates: Sequence[str] = (str(RDFS.subClassOf),)


class OwlIngestor(Ingestor):
    """Load Semra artifacts from OWL ontologies."""

    def __init__(self, path: Path, settings: OwlIngestorSettings | None = None) -> None:
        super().__init__(path)
        self.settings = settings or OwlIngestorSettings()

    def load(self) -> Iterable[Artifact]:
        graph = Graph()
        graph.parse(self.path.as_posix())

        label_predicates = [URIRef(uri) for uri in self.settings.label_predicates]
        synonym_predicates = [URIRef(uri) for uri in self.settings.synonym_predicates]
        definition_predicates = [URIRef(uri) for uri in self.settings.definition_predicates]
        namespace_predicates = [URIRef(uri) for uri in self.settings.namespace_predicates]
        relationship_predicates = [URIRef(uri) for uri in self.settings.relationship_predicates]

        artifacts: List[Artifact] = []
        for subject in graph.subjects(RDF.type, OWL.Class):
            identifier = self._resolve_identifier(graph, subject)
            name = self._first_literal(graph, subject, label_predicates) or identifier
            description = self._first_literal(graph, subject, definition_predicates)

            attributes = {
                "iri": str(subject),
            }
            namespace = self._first_literal(graph, subject, namespace_predicates)
            if namespace:
                attributes["namespace"] = namespace

            synonyms = sorted(set(self._collect_literals(graph, subject, synonym_predicates)))

            provenance = [
                ProvenanceRecord(
                    source=str(self.path),
                    recorded_at=_now_utc(),
                    note="Ingested from OWL",
                )
            ]

            relationships = self._collect_relationships(
                graph, subject, relationship_predicates, provenance
            )

            artifact = Artifact(
                identifier=identifier,
                artifact_type=self.settings.artifact_type,
                name=name,
                description=description,
                attributes=attributes,
                synonyms=synonyms,
                relationships=relationships,
                provenance=provenance,
            )
            artifacts.append(artifact)

        LOGGER.info(
            "Loaded %d artifacts from %s", len(artifacts), self.path.name
        )
        return artifacts

    def _resolve_identifier(self, graph: Graph, subject: URIRef) -> str:
        for literal in graph.objects(subject, OBO_IN_OWL.id):
            if isinstance(literal, Literal):
                return str(literal)
        curie = _curie_from_iri(subject)
        return curie or str(subject)

    def _first_literal(
        self, graph: Graph, subject: URIRef, predicates: Sequence[URIRef]
    ) -> str | None:
        for predicate in predicates:
            for literal in graph.objects(subject, predicate):
                if isinstance(literal, Literal):
                    return str(literal)
        return None

    def _collect_literals(
        self, graph: Graph, subject: URIRef, predicates: Sequence[URIRef]
    ) -> List[str]:
        values: List[str] = []
        for predicate in predicates:
            for literal in graph.objects(subject, predicate):
                if isinstance(literal, Literal):
                    values.append(str(literal))
        return values

    def _collect_relationships(
        self,
        graph: Graph,
        subject: URIRef,
        predicates: Sequence[URIRef],
        provenance: List[ProvenanceRecord],
    ) -> List[Relationship]:
        relationships: List[Relationship] = []
        for predicate in predicates:
            for target in graph.objects(subject, predicate):
                if not isinstance(target, URIRef):
                    continue
                target_id = self._resolve_identifier(graph, target)
                relationships.append(
                    Relationship(
                        predicate=str(predicate),
                        target_id=target_id,
                        provenance=list(provenance),
                    )
                )
        return relationships


def _curie_from_iri(iri: URIRef) -> str | None:
    text = str(iri)
    if text.startswith("http://purl.obolibrary.org/obo/"):
        suffix = text.split("obo/")[-1]
        if "_" in suffix:
            prefix, local = suffix.split("_", 1)
            return f"{prefix}:{local}"
    return None


def _now_utc():
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc)


__all__ = ["OwlIngestor", "OwlIngestorSettings"]

