from loguru import logger

from config import Backup
from worker.compression import compress_file
from worker.db import dump_db
from worker.file import delete_file, move_file_to_folder, get_backup_file
from worker.backup import upload_backup, remove_old_backups
from worker.security import encrypt_file


def backup_task(backup: Backup):
    logger.info(f"[{backup.name}] Starting backup task...")
    dump_file = None
    compressed_dump_file = None
    encrypted_dump_file = None
    try:
        backup_file_prefix, backup_filename, backup_filepath = get_backup_file(
            backup.name, backup.filename, backup.date_format
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
        protocol = backup.host_obj.protocol if not backup.local else "local"

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

        logger.success(f"[{backup.name}] Backup task completed successfully")
    except Exception as e:
        logger.error(f"[{backup.name}] Backup task failed: {e}")
    finally:
        if dump_file:
            delete_file(dump_file)
        if compressed_dump_file:
            delete_file(compressed_dump_file)
        if encrypted_dump_file:
            delete_file(encrypted_dump_file)
