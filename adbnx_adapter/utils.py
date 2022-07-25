import logging
import os

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

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
