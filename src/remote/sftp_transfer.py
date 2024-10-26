import os
import paramiko
from loguru import logger
from config import Host


def send_file_over_sftp(
    local_filepath: str, remote_dir_path: str, remote_filename: str, host: Host
):
    """
    Sends a file over SFTP to a remote host.

    :param local_filepath: Path to the local file to send.
    :param remote_dir_path: Destination directory path on the remote host.
    :param remote_filename: Name of the file on the remote host.
    :param host: Host configuration including hostname, port, username, and password.
    """

    remote_filepath = os.path.join(remote_dir_path, remote_filename)
    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over SFTP: {local_filepath} -> {remote_dest}")

    try:
        transport = paramiko.Transport((host.host, host.port))
        transport.connect(username=host.username, password=host.password)

        sftp = paramiko.SFTPClient.from_transport(transport)

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
        transport.close()

        logger.info(f"File sent successfully over SFTP to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over SFTP: {e}, {remote_dest}")
        raise
