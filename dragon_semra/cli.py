"""Command-line interface for the Dragon-Semra pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from dragon_semra.pipeline import run_from_config

LOGGER = logging.getLogger("dragon_semra")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Dragon-Semra enrichment pipeline")
    parser.add_argument("config", type=Path, help="Path to a pipeline YAML configuration file")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Verbosity for log output",
    )

    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    LOGGER.info("Starting pipeline with configuration %s", args.config)
    try:
        run_from_config(args.config)
    except Exception as exc:  # pragma: no cover - CLI level
        LOGGER.exception("Pipeline execution failed: %s", exc)
        return 1

    LOGGER.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
