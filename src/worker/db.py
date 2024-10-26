import os
import subprocess
import tempfile
from datetime import datetime
from loguru import logger
from config import Backup


def get_backup_file_path(backup_name: str, backup_filename: str = None):
    tmp_dir = tempfile.gettempdir()
    prefix = backup_filename if backup_filename else f"{backup_name}"
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
    return os.path.join(tmp_dir, filename)


def dump_db(
    backup: Backup,
):
    db_connection = backup.db_connection_obj
    logger.info(f"Dumping database: {db_connection.name} ({db_connection.database})")
    cnf_file_path = None
    backup_file_path = get_backup_file_path(backup.name, backup.filename)

    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as cnf_file:
            cnf_file.write(
                f"""[client]
host={db_connection.host}
user={db_connection.username}
password={db_connection.password}
port={db_connection.port}
"""
            )
            cnf_file_path = cnf_file.name

        command = [
            "mysqldump",
            f"--defaults-extra-file={cnf_file_path}",
            "--no-tablespaces",
            db_connection.database,
        ]

        if backup.skip_tables:
            skip_tables_list = backup.skip_tables.split(",")
            command.extend(
                f"--ignore-table={db_connection.database}.{table}"
                for table in skip_tables_list
            )

        with open(backup_file_path, "w") as backup_file:
            result = subprocess.run(
                command,
                stdout=backup_file,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

            if result.stderr:
                logger.error(f"mysqldump error: {result.stderr.strip()}")
                raise Exception(f"mysqldump failed with error: {result.stderr.strip()}")

            logger.info(f"Database dump saved to: {backup_file_path}")
            return backup_file_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Database dump failed: {e}")
        raise e
    finally:
        if cnf_file_path and os.path.exists(cnf_file_path):
            os.remove(cnf_file_path)
