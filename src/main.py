import time
from datetime import datetime
from config import get_config, Backup
from scheduler import start_scheduler

def backup_task(backup : Backup):
    print(f"[{datetime.now()}] Starting backup: {backup.name}({backup.protocol}) ")
    time.sleep(2)  

if __name__ == '__main__':
    config = get_config("../config.yaml")
    start_scheduler(backup_task, config)
    print(config)