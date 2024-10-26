import os
import paramiko
from scp import SCPClient
from loguru import logger
from config import Host


def send_file_over_ssh_with_scp(
    local_filepath: str, remote_dir_path: str, remote_filename: str, host: Host
):
    """
    Sends a file over SSH to a remote host using SCP.

    :param local_filepath: Path to the local file to send.
    :param remote_dir_path: Destination directory path on the remote host.
    :param remote_filename: Name of the file on the remote host.
    :param host: Host configuration including hostname, port, username, and password.
    """

    remote_filepath = os.path.join(remote_dir_path, remote_filename)
    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over SSH using SCP: {local_filepath} -> {remote_dest}")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=host.host,
            port=host.port,
            username=host.username,
            password=host.password,
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
