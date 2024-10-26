from loguru import logger
from config import get_config, Backup, Log
from scheduler import start_scheduler
from worker.db import dump_db
from worker.compression import compress_file
from worker.security import encrypt_file
from worker.file import delete_file, move_file_to_folder
from remote.remote_transfer import remote_transfer


def backup_task(backup: Backup):
    logger.info(f"Starting backup task for {backup.name}")
    dump_file = None
    compressed_dump_file = None
    encrypted_dump_file = None
    try:
        dump_file = dump_db(backup)

        if backup.compression_enabled:
            compressed_dump_file = compress_file(dump_file)

        if backup.encryption_enabled:
            file_to_encrypt = compressed_dump_file or dump_file
            encrypted_dump_file = encrypt_file(
                file_to_encrypt, backup.encryption_password
            )

        file_to_send = encrypted_dump_file or compressed_dump_file or dump_file
        if backup.local:
            move_file_to_folder(
                file_to_send,
                backup.path,
            )
        else:
            remote_transfer(
                backup.host_obj.protocol,
                file_to_send,
                backup.path,
                backup.host_obj,
            )

    except Exception as e:
        logger.error(f"Backup failed: {e}")
    finally:
        if dump_file:
            delete_file(dump_file)
        if compressed_dump_file:
            delete_file(compressed_dump_file)
        if encrypted_dump_file:
            delete_file(encrypted_dump_file)


def setup_logger(config: Log):
    logger.add(
        config.file,
        level=config.level,
        rotation=config.rotation_interval,
        retention=config.retention_period,
    )


if __name__ == "__main__":
    config = get_config("config.yaml")
    setup_logger(config.log)
    start_scheduler(backup_task, config)
