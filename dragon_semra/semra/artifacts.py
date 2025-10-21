"""Semra-inspired artifact data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ProvenanceRecord:
    """Represents provenance metadata for an artifact attribute."""

    source: str
    recorded_at: datetime
    note: Optional[str] = None


@dataclass
class Relationship:
    """Describes a typed relationship between two artifacts."""

    predicate: str
    target_id: str
    confidence: float = 1.0
    provenance: List[ProvenanceRecord] = field(default_factory=list)


@dataclass
class Artifact:
    """Container matching the structure of a Semra artifact."""

    identifier: str
    artifact_type: str
    name: str
    description: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    synonyms: List[str] = field(default_factory=list)
    acronyms: List[str] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    provenance: List[ProvenanceRecord] = field(default_factory=list)


__all__ = ["Artifact", "Relationship", "ProvenanceRecord"]
