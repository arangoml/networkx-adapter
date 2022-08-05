import logging
import os
from typing import Any, Union

from arango.aql import Cursor
from networkx.classes.graph import EdgeView, NodeView
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, track

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


def track_adb(cursor: Cursor, text: str, colour: str) -> Any:
    return track(
        cursor,
        total=cursor.count(),
        description=text,
        complete_style=colour,
        finished_style=colour,
        disable=logger.level != logging.INFO,
    )


def track_nx(nx_data: Union[NodeView, EdgeView], text: str, colour: str) -> Any:
    return track(
        nx_data,
        description=text,
        complete_style=colour,
        finished_style=colour,
        disable=logger.level != logging.INFO,
    )
