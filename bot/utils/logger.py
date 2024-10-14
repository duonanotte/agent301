import sys
from loguru import logger

logger.remove()

logger.add(
    sink=sys.stdout,
    format=(
        "<green><b>[Agent301]</b></green> "
        "| <white>{time:HH:mm:ss}</white> "
        "| <level>{level: <8}</level> "
        "| <white><b>{message}</b></white>"
    ),
    colorize=True
)

logger = logger.opt(colors=True)