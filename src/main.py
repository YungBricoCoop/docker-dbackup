import time
from datetime import datetime
from loguru import logger
from config import get_config, Backup, Log
from scheduler import start_scheduler

def backup_task(backup : Backup):
    logger.info(f"Starting backup: {backup.name}({backup.protocol}) ")
    time.sleep(2)  

def setup_logger(config : Log):
    logger.add(
        config.file,
        level=config.level,
        rotation=config.rotation_interval,
        retention=config.retention_period
    )

if __name__ == '__main__':
    config = get_config("../config.yaml")
    setup_logger(config.log)
    start_scheduler(backup_task, config)
    print(config)