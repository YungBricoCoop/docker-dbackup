import os
from datetime import datetime
from ftplib import FTP, error_perm

import paramiko
from loguru import logger
from scp import SCPClient

from config import Host
from worker.file import get_filename_from_path

DEFAULT_TIMEOUT_IN_SECONDS = 10


def remote_transfer(
    type: str,
    local_filepath: str,
    remote_dir_path: str,
    host: Host,
):
    remote_filename = get_filename_from_path(local_filepath)
    if type == "scp":
        send_file_over_ssh_with_scp(
            local_filepath, remote_dir_path, remote_filename, host
        )
    elif type == "sftp":
        send_file_over_sftp(local_filepath, remote_dir_path, remote_filename, host)
    elif type == "ftp":
        send_file_over_ftp(local_filepath, remote_dir_path, remote_filename, host)


def remote_remove_old_backups(
    type: str,
    remote_dir_path: str,
    filename_prefix: str,
    date_format: str,
    max_backup_files: int,
    host: Host,
):
    if type == "scp":
        remove_old_backups_scp(
            remote_dir_path, filename_prefix, date_format, max_backup_files, host
        )
    elif type == "sftp":
        remove_old_backups_sftp(
            remote_dir_path, filename_prefix, date_format, max_backup_files, host
        )
    elif type == "ftp":
        remove_old_backups_ftp(
            remote_dir_path, filename_prefix, date_format, max_backup_files, host
        )


def get_ssh_client(host: Host):
    """
    Creates an SSH client with the provided host configuration.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if host.password:
        ssh.connect(
            hostname=host.host,
            port=host.port,
            username=host.username,
            password=host.password,
            timeout=DEFAULT_TIMEOUT_IN_SECONDS,
        )
    elif host.private_ssh_key:
        ssh.connect(
            hostname=host.host,
            port=host.port,
            username=host.username,
            key_filename=host.private_ssh_key,
            timeout=DEFAULT_TIMEOUT_IN_SECONDS,
        )

    return ssh


def get_ftp_client(host: Host):
    """
    Creates an FTP client with the provided host configuration.
    """
    ftp = FTP()
    ftp.connect(host.host, host.port, timeout=DEFAULT_TIMEOUT_IN_SECONDS)
    ftp.login(user=host.username, passwd=host.password)
    return ftp


def send_file_over_ssh_with_scp(
    local_filepath: str, remote_dir_path: str, remote_filename: str, host: Host
):
    """
    Sends a file over SSH to a remote host using SCP.

    :param local_filepath: Path to the local file to send.
    :param remote_dir_path: Destination directory path on the remote host.
    :param remote_filename: Name of the file on the remote host.
    :param host: Host configuration including hostname, port, username, password, or private SSH key.
    """

    remote_filepath = os.path.join(remote_dir_path, remote_filename)
    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over SSH using SCP: {local_filepath} -> {remote_dest}")

    try:
        ssh = get_ssh_client(host)

        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p '{remote_dir_path}'")
        stdout.channel.recv_exit_status()

        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_filepath, remote_filepath)

        logger.info(f"File sent successfully over SSH to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over SSH using SCP: {e}")
        raise
    finally:
        ssh.close()


def send_file_over_sftp(
    local_filepath: str, remote_dir_path: str, remote_filename: str, host: Host
):
    """
    Sends a file over SFTP to a remote host.

    :param local_filepath: Path to the local file to send.
    :param remote_dir_path: Destination directory path on the remote host.
    :param remote_filename: Name of the file on the remote host.
    :param host: Host configuration including hostname, port, username, password, or private SSH key.
    """

    remote_filepath = os.path.join(remote_dir_path, remote_filename)
    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over SFTP: {local_filepath} -> {remote_dest}")

    try:
        ssh = get_ssh_client(host)

        sftp = ssh.open_sftp()

        try:
            sftp.chdir(remote_dir_path)
        except IOError:
            dir_paths = remote_dir_path.strip("/").split("/")
            current_dir = ""
            for dir in dir_paths:
                current_dir += f"/{dir}"
                try:
                    sftp.mkdir(current_dir)
                except IOError:
                    pass
                sftp.chdir(current_dir)

        sftp.put(local_filepath, remote_filepath)

        sftp.close()
        ssh.close()

        logger.info(f"File sent successfully over SFTP to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over SFTP: {e}, {remote_dest}")
        raise


def create_ftp_directory_tree(ftp, remote_dir):
    """
    Creates directories recursively on the FTP server.

    :param ftp: Active FTP connection.
    :param remote_dir: Remote directory path to create.
    """
    dirs = remote_dir.strip("/").split("/")
    current_dir = ""
    for dir in dirs:
        current_dir += f"/{dir}"
        try:
            ftp.cwd(current_dir)
        except error_perm:
            ftp.mkd(current_dir)


def send_file_over_ftp(
    local_filepath: str, remote_dir_path: str, remote_filename: str, host: Host
):
    """
    Sends a file over FTP to a remote server.

    :param local_filepath: Path to the local file to send.
    :param remote_dir_path: Destination directory path on the remote server.
    :param remote_filename: Name of the file on the remote server.
    :param host: Host configuration including hostname, port, username, and password.
    """

    remote_filepath = os.path.join(remote_dir_path, remote_filename)
    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over FTP: {local_filepath} -> {remote_dest}")

    try:
        ftp = get_ftp_client(host)

        if remote_dir_path:
            try:
                ftp.cwd(remote_dir_path)
            except error_perm:
                create_ftp_directory_tree(ftp, remote_dir_path)
                ftp.cwd(remote_dir_path)

        with open(local_filepath, "rb") as file:
            ftp.storbinary(f"STOR {remote_filename}", file)

        ftp.quit()

        logger.info(f"File sent successfully over FTP to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over FTP: {e}, {remote_dest}")
        raise


def get_file_date_from_filename(filename: str, filename_prefix: str, date_format: str):
    """
    Extracts the date from a backup file name.

    :param filename: The backup file name.
    :param filename_prefix: The prefix of the backup file name.
    :param date_format: The date format used in the backup file name.
    :return: The date extracted from the file name.
    """
    try:
        date_str = filename[len(filename_prefix) :]
        date_str = date_str.split(".sql")[0]
        return datetime.strptime(date_str, date_format)
    except Exception as e:
        logger.error(f"Failed to extract date from filename '{filename}': {e}")
        return None


def get_files_to_delete(files, filename_prefix, date_format, max_backup_files):
    """
    Returns a list of files to delete based on the max_backup_files limit.

    :param files: List of backup files.
    :param filename_prefix: Prefix of the backup filenames.
    :param date_format: Date format used in the backup filenames.
    :param max_backup_files: Maximum number of backup files to keep.
    :return: List of files to delete.
    """
    if not files:
        return []

    files = [file for file in files if file.startswith(filename_prefix)]
    files_to_delete = []

    for file in files:
        date = get_file_date_from_filename(file, filename_prefix, date_format)
        if not date:
            continue
        files_to_delete.append((date, file))

    files_to_delete.sort()
    if len(files_to_delete) > max_backup_files:
        return [file for _, file in files_to_delete[:-max_backup_files]]
    return []


def remove_old_backups_scp(
    remote_dir_path: str,
    filename_prefix: str,
    date_format: str,
    max_backup_files: int,
    host: Host,
):
    """
    Removes old backup files over SSH (SCP) that exceed the max_backup_files limit.

    :param remote_dir_path: Remote directory path where backups are stored.
    :param filename_prefix: Prefix of the backup filenames to identify relevant files.
    :param date_format: Date format used in the backup filenames.
    :param max_backup_files: Maximum number of backup files to keep.
    :param host: Host configuration including hostname, port, username, password, or private SSH key.
    """

    try:
        ssh = get_ssh_client(host)

        stdin, stdout, stderr = ssh.exec_command(f"ls -1 {remote_dir_path}")
        files = stdout.read().decode().splitlines()

        files_to_delete = get_files_to_delete(
            files, filename_prefix, date_format, max_backup_files
        )

        if len(files_to_delete) == 0:
            ssh.close()
            return
        for file in files_to_delete:
            remote_file_path = os.path.join(remote_dir_path, file)
            print(remote_file_path)
            try:
                ssh.exec_command(f"rm '{remote_file_path}'")
                logger.info(f"Deleted old backup file: {remote_file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file '{remote_file_path}': {e}")

        ssh.close()
    except Exception as e:
        logger.error(f"Failed to remove old backups over SSH: {e}")
        raise


def remove_old_backups_sftp(
    remote_dir_path: str,
    filename_prefix: str,
    date_format: str,
    max_backup_files: int,
    host: Host,
):
    """
    Removes old backup files over SFTP that exceed the max_backup_files limit.

    :param remote_dir_path: Remote directory path where backups are stored.
    :param filename_prefix: Prefix of the backup filenames to identify relevant files.
    :param date_format: Date format used in the backup filenames.
    :param max_backup_files: Maximum number of backup files to keep.
    :param host: Host configuration including hostname, port, username, password, or private SSH key.
    """

    try:
        ssh = get_ssh_client(host)

        sftp = ssh.open_sftp()
        sftp.chdir(remote_dir_path)
        files = sftp.listdir()

        files_to_delete = get_files_to_delete(
            files, filename_prefix, date_format, max_backup_files
        )
        if len(files_to_delete) == 0:
            sftp.close()
            ssh.close()
            return

        for file in files_to_delete:
            remote_file_path = os.path.join(remote_dir_path, file)
            try:
                sftp.remove(remote_file_path)
                logger.info(f"Deleted old backup file: {remote_file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file '{remote_file_path}': {e}")

        sftp.close()
        ssh.close()
    except Exception as e:
        logger.error(f"Failed to remove old backups over SFTP: {e}")
        raise


def remove_old_backups_ftp(
    remote_dir_path: str,
    filename_prefix: str,
    date_format: str,
    max_backup_files: int,
    host: Host,
):
    """
    Removes old backup files over FTP that exceed the max_backup_files limit.

    :param remote_dir_path: Remote directory path where backups are stored.
    :param filename_prefix: Prefix of the backup filenames to identify relevant files.
    :param date_format: Date format used in the backup filenames.
    :param max_backup_files: Maximum number of backup files to keep.
    :param host: Host configuration including hostname, port, username, and password.
    """

    try:
        ftp = get_ftp_client(host)
        ftp.cwd(remote_dir_path)
        files = ftp.nlst()

        files_to_delete = get_files_to_delete(
            files, filename_prefix, date_format, max_backup_files
        )

        if len(files_to_delete) == 0:
            ftp.quit()
            return

        for file in files_to_delete:
            try:
                ftp.delete(file)
                logger.info(f"Deleted old backup file: {file}")
            except Exception as e:
                logger.error(f"Failed to delete file '{file}': {e}")

        ftp.quit()
    except Exception as e:
        logger.error(f"Failed to remove old backups over FTP: {e}")
        raise
