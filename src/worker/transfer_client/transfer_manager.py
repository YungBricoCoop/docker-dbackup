import os

from loguru import logger

from worker.file import get_backups_to_delete, get_filename_from_path
from worker.transfer_client.scp_transfer import SCPTransferClient
from worker.transfer_client.sftp_transfert import SFTPTransferClient
from worker.transfer_client.ftp_transfer import FTPTransferClient
from worker.transfer_client.local_transfer import LocalTransferClient


def get_client(client_type: str, host=None):
    if client_type == "scp":
        return SCPTransferClient(host)
    elif client_type == "sftp":
        return SFTPTransferClient(host)
    elif client_type == "ftp":
        return FTPTransferClient(host)
    elif client_type == "local":
        return LocalTransferClient()
    else:
        raise ValueError(f"Unknown client_type: {client_type}")


def upload_backup(
    client_type: str,
    local_filepath: str,
    remote_dir_path: str,
    host,
):
    client = get_client(client_type, host)
    client.connect()
    try:
        client.mkdir(remote_dir_path)
        remote_filename = get_filename_from_path(local_filepath)
        remote_filepath = os.path.join(remote_dir_path, remote_filename)
        client.upload_file(local_filepath, remote_filepath)
    except Exception as e:
        logger.error(f"Failed to send file: {e}")
        raise
    finally:
        client.disconnect()


def remove_old_backups(
    client_type: str,
    remote_dir_path: str,
    filename_prefix: str,
    date_format: str,
    max_backup_files: int,
    host,
):
    client = get_client(client_type, host)
    client.connect()
    try:
        files = client.list_files(remote_dir_path)
        files_to_delete = get_backups_to_delete(
            files, filename_prefix, date_format, max_backup_files
        )
        if not files_to_delete:
            return
        for file in files_to_delete:
            remote_file_path = os.path.join(remote_dir_path, file)
            client.delete_file(remote_file_path)
            logger.info(f"Deleted old backup file: {remote_file_path}")
    except Exception as e:
        logger.error(f"Failed to remove old backups: {e}")
        raise
    finally:
        client.disconnect()
