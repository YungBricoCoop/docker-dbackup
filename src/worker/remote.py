import os
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
        ftp = FTP()
        ftp.connect(host=host.host, port=host.port, timeout=DEFAULT_TIMEOUT_IN_SECONDS)
        ftp.login(user=host.username, passwd=host.password)

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
