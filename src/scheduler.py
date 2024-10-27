import time
from config import Config
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


def start_scheduler(backup_task, config: Config):
    logger.info("Starting scheduler...")
    scheduler = BackgroundScheduler()
    for backup in config.backup:
        trigger = CronTrigger.from_crontab(backup.schedule)
        scheduler.add_job(backup_task, trigger=trigger, args=[backup], id=backup.name)
    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
