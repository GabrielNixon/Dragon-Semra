"""Ingestion interfaces for pipeline sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from dragon_semra.semra.artifacts import Artifact


class Ingestor(ABC):
    """Abstract base class for ingestion components."""

    def __init__(self, path: Path):
        self.path = Path(path)

    @abstractmethod
    def load(self) -> Iterable[Artifact]:
        """Yield :class:`Artifact` instances from the source."""


__all__ = ["Ingestor"]
