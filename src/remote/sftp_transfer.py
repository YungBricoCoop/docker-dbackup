import os
import paramiko
from loguru import logger
from config import Host


def send_file_over_sftp(local_filepath, remote_filepath, host: Host):
    """
    Sends a file over SFTP to a remote host.

    :param local_filepath: Path to the local file to send.
    :param remote_filepath: Destination path on the remote host.
    :param host: Hostname or IP address of the SFTP server.
    :param port: SFTP port number (default is 22).
    :param username: SFTP username.
    :param password: SFTP password.
    """

    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over SFTP: {local_filepath} -> {remote_dest}")

    try:
        transport = paramiko.Transport((host.host, host.port))
        transport.connect(username=host.username, password=host.password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_dir = os.path.dirname(remote_filepath)
        try:
            sftp.chdir(remote_dir)
        except IOError:
            sftp.chdir(remote_dir)

        sftp.put(local_filepath, remote_filepath)

        sftp.close()
        transport.close()

        logger.info(f"File sent successfully over SFTP to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over SFTP: {e}, {remote_dest}")
        raise
