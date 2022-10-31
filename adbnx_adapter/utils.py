import logging
import os
from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.progress import track as progress_track

logger = logging.getLogger(__package__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    f"[%(asctime)s] [{os.getpid()}] [%(levelname)s] - %(name)s: %(message)s",
    "%Y/%m/%d %H:%M:%S %z",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def progress(
    text: str,
    spinner_name: str = "aesthetic",
    spinner_style: str = "#5BC0DE",
) -> Progress:
    return Progress(
        TextColumn(text),
        SpinnerColumn(spinner_name, spinner_style),
        TimeElapsedColumn(),
        transient=True,
    )


def track(sequence: Any, total: int, text: str, colour: str) -> Any:
    return progress_track(
        sequence,
        total=total,
        description=text,
        complete_style=colour,
        finished_style=colour,
        disable=logger.level != logging.INFO,
    )
