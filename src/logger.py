import sys
from loguru import logger
from config import Log


def setup_logger(config: Log):
    logger.remove()
    logger.add(
        config.filename,
        level=config.level,
        rotation=config.rotation_interval,
        retention=config.retention_period,
        format=config.format,
    )
    logger.add(sys.stdout, level=config.level, format=config.format, colorize=True)
