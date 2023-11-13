import logging
import os

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

logger = logging.getLogger(__package__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    f"[%(asctime)s] [{os.getpid()}] [%(levelname)s] - %(name)s: %(message)s",
    "%Y/%m/%d %H:%M:%S %z",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_export_spinner_progress(text: str) -> Progress:
    return Progress(
        TextColumn(text),
        SpinnerColumn("aesthetic", "#5BC0DE"),
        TimeElapsedColumn(),
        transient=True,
    )


def get_import_spinner_progress(text: str) -> Progress:
    return Progress(
        TextColumn(text),
        TextColumn("{task.fields[action]}"),
        SpinnerColumn("aesthetic", "#5BC0DE"),
        TimeElapsedColumn(),
        transient=True,
    )


def get_bar_progress(text: str, color: str) -> Progress:
    return Progress(
        TextColumn(text),
        BarColumn(complete_style=color, finished_style=color),
        TaskProgressColumn(),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
    )
