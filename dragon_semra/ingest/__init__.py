"""Ingestion components."""

from .base import Ingestor
from .csv_loader import CsvIngestor

__all__ = ["Ingestor", "CsvIngestor"]
