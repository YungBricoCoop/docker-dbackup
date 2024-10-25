import os
from ftplib import FTP, error_perm
from loguru import logger
from config import Host


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


def send_file_over_ftp(local_filepath, remote_filepath, host: Host):
    """
    Sends a file over FTP to a remote server.

    :param local_filepath: Path to the local file to send.
    :param remote_filepath: Destination path on the remote server.
    :param host: Hostname or IP address of the FTP server.
    :param port: FTP port number (default is 21).
    :param username: FTP username.
    :param password: FTP password.
    """

    remote_dest = f"{host.username}@{host.host}:{remote_filepath}"
    logger.info(f"Sending file over FTP: {local_filepath} -> {remote_dest}")

    try:
        ftp = FTP()
        ftp.connect(host=host.host, port=host.port)
        ftp.login(user=host.username, passwd=host.password)

        remote_dir = os.path.dirname(remote_filepath)
        if remote_dir:
            try:
                ftp.cwd(remote_dir)
            except error_perm:
                create_ftp_directory_tree(ftp, remote_dir)
                ftp.cwd(remote_dir)
        # FIXME: The file get's written as the folder name
        with open(local_filepath, "rb") as file:
            ftp.storbinary(f"STOR {os.path.basename(remote_filepath)}", file)

        ftp.quit()

        logger.info(f"File sent successfully over FTP to {remote_dest}")
    except Exception as e:
        logger.error(f"Failed to send file over FTP: {e}, {remote_dest}")
        raise
