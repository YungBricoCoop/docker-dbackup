import paramiko
from scp import SCPClient
from loguru import logger
from config import Host


def send_file_over_ssh(local_filepath, remote_filepath, host: Host):
    """
    Sends a file over SSH to a remote host using SCP.

    :param local_filepath: Path to the local file to send.
    :param remote_filepath: Destination path on the remote host.
    :param host: Host configuration including hostname, port, username, and password.
    """

    logger.info(
        f"Sending file over SSH using SCP: {local_filepath} -> {host.username}@{host.host}:{remote_filepath}"
    )

    try:
        # Initialize SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the host
        ssh.connect(
            hostname=host.host,
            port=host.port,
            username=host.username,
            password=host.password,
        )

        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_filepath, remote_filepath)

        logger.info(
            f"File sent successfully over SSH to {host.username}@{host.host}:{remote_filepath}"
        )
    except Exception as e:
        logger.error(f"Failed to send file over SSH using SCP: {e}")
        raise
    finally:
        ssh.close()
