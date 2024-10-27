from loguru import logger

from config import Backup
from worker.backup import remove_old_backups, upload_backup
from worker.compression import compress_file
from worker.db import dump_db
from worker.file import delete_file, get_backup_file
from worker.notification import send_notifications
from worker.security import encrypt_file
from data import BackupData


def backup_task(backup: Backup):
    logger.info(f"[{backup.id}] Starting backup task...")

    dump_file = None
    compressed_dump_file = None
    encrypted_dump_file = None
    protocol = backup.host_obj.protocol if not backup.local else "local"
    host = backup.host_obj.hostname if not backup.local else "local"

    backup_data = BackupData.BackupData(
        backup.id,
        backup.db_connection_obj.database,
        host,
        protocol,
        backup.compression_enabled,
        backup.encryption_enabled,
    )

    try:
        backup_file_prefix, backup_filename, backup_filepath = get_backup_file(
            backup.id, backup.filename, backup.date_format
        )
        dump_file = dump_db(backup, backup_filepath)

        if backup.compression_enabled:
            compressed_dump_file = compress_file(dump_file)

        if backup.encryption_enabled:
            file_to_encrypt = compressed_dump_file or dump_file
            encrypted_dump_file = encrypt_file(
                file_to_encrypt, backup.encryption_password
            )

        file_to_send = encrypted_dump_file or compressed_dump_file or dump_file

        upload_backup(
            protocol,
            file_to_send,
            backup.path,
            backup.host_obj,
        )
        remove_old_backups(
            protocol,
            backup.path,
            backup_file_prefix,
            backup.date_format,
            backup.max_backup_files,
            backup.host_obj,
        )

        backup_data.set_status(success=True)
        logger.success(backup_data.status_short)
        send_notifications(
            backup_data=backup_data,
            notifications=backup.notification_objs,
        )

    except Exception as e:
        backup_data.set_status(success=False, error=str(e))
        logger.error(backup_data.status_short)
        send_notifications(
            backup_data=backup_data,
            notifications=backup.notification_objs,
        )
    finally:
        if dump_file:
            delete_file(dump_file)
        if compressed_dump_file:
            delete_file(compressed_dump_file)
        if encrypted_dump_file:
            delete_file(encrypted_dump_file)
