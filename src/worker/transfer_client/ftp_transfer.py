import os
from ftplib import FTP, error_perm

from worker.transfer_client.base import TransferClient


class FTPTransferClient(TransferClient):
    def __init__(self, host):
        self.host = host
        self.ftp = None

    def connect(self):
        self.ftp = FTP()
        self.ftp.connect(
            self.host.hostname,
            self.host.port,
            timeout=TransferClient.DEFAULT_TIMEOUT_IN_SECONDS,
        )
        self.ftp.login(user=self.host.username, passwd=self.host.password)

    def disconnect(self):
        if self.ftp:
            self.ftp.quit()
            self.ftp = None

    def upload_file(self, local_path, remote_path):
        remote_dir, remote_filename = os.path.split(remote_path)
        self.mkdir(remote_dir)
        self.chdir(remote_dir)
        with open(local_path, "rb") as file:
            self.ftp.storbinary(f"STOR {remote_filename}", file)

    def mkdir(self, path):
        dirs = path.strip("/").split("/")
        current_dir = ""
        for cdir in dirs:
            current_dir += f"/{cdir}"
            try:
                self.ftp.cwd(current_dir)
            except error_perm:
                self.ftp.mkd(current_dir)

    def chdir(self, path):
        self.ftp.cwd(path)

    def delete_file(self, path):
        self.ftp.delete(path)

    def list_files(self, path):
        self.ftp.cwd(path)
        return self.ftp.nlst()
