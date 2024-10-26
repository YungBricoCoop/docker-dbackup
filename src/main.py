import sys

from config import get_config
from logger import setup_logger
from scheduler import start_scheduler
from worker import tasks

if __name__ == "__main__":
    config = get_config("config.yaml")
    if not config:
        sys.exit(1)
    setup_logger(config.log)
    start_scheduler(tasks.backup_task, config)
