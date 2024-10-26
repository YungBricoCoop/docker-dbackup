from remote import ssh_transfer, sftp_transfer, ftp_transfer
from config import Host
from worker.file import get_filename_from_path


def remote_transfer(
    type: str,
    local_filepath: str,
    remote_dir_path: str,
    host: Host,
):
    remote_filename = get_filename_from_path(local_filepath)
    if type == "ssh":
        ssh_transfer.send_file_over_ssh(
            local_filepath, remote_dir_path, remote_filename, host
        )
    elif type == "sftp":
        sftp_transfer.send_file_over_sftp(
            local_filepath, remote_dir_path, remote_filename, host
        )
    elif type == "ftp":
        ftp_transfer.send_file_over_ftp(
            local_filepath, remote_dir_path, remote_filename, host
        )
