import time
from loguru import logger
from config import get_config, Backup, Log
from scheduler import start_scheduler
from worker.db import dump_db
from worker.compression import compress_file



def backup_task(backup : Backup):
    time.sleep(2)  

def setup_logger(config : Log):
    logger.add(
        config.file,
        level=config.level,
        rotation=config.rotation_interval,
        retention=config.retention_period
    )

if __name__ == '__main__':
    config = get_config("config.yaml")
    dump_file = dump_db(config.db_connections[0])
    compressed_dump_file = compress_file(dump_file)
    print(compressed_dump_file)
    setup_logger(config.log)
    start_scheduler(backup_task, config)
    print(config)