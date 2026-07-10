from __future__ import annotations

import logging

from .config import Config
from .instrumentation import instrument_module_functions


def configure_logging(config: Config) -> None:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(config.log_dir / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


instrument_module_functions(globals())
