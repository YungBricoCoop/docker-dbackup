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
        ftp.connect(host=host.host, port=host.port)
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
