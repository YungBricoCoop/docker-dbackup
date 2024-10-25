import os
import paramiko
from loguru import logger
from config import Host


def send_file_over_ssh(local_filepath, remote_filepath, host: Host):
    """
    Sends a file over SSH to a remote host using SFTP.

    :param local_filepath: Path to the local file to send.
    :param remote_filepath: Destination path on the remote host.
    :param host: Hostname or IP address of the remote host.
    :param port: SSH port number (default is 22).
    :param username: SSH username.
    :param password: SSH password.
    """

    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over SSH: {local_filepath} -> {remote_dest}")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=host.host,
            port=host.port,
            username=host.username,
            password=host.password,
        )

        sftp = ssh.open_sftp()

        remote_dir = os.path.dirname(remote_filepath)
        try:
            sftp.chdir(remote_dir)
        except IOError:
            sftp.makedirs(remote_dir)
            sftp.chdir(remote_dir)

        sftp.put(local_filepath, remote_filepath)

        sftp.close()
        ssh.close()

        logger.info(f"File sent successfully over SSH to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over SSH: {e}, {remote_dest}")
        raise
