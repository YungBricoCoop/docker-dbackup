import paramiko

from worker.transfer_client.base import TransferClient


class SFTPTransferClient(TransferClient):
    def __init__(self, host):
        self.host = host
        self.ssh = None
        self.sftp = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.host.password:
            self.ssh.connect(
                hostname=self.host.hostname,
                port=self.host.port,
                username=self.host.username,
                password=self.host.password,
                timeout=TransferClient.DEFAULT_TIMEOUT_IN_SECONDS,
            )
        elif self.host.ssh_key:
            self.ssh.connect(
                hostname=self.host.hostname,
                port=self.host.port,
                username=self.host.username,
                key_filename=self.host.ssh_key,
                timeout=TransferClient.DEFAULT_TIMEOUT_IN_SECONDS,
            )

        self.sftp = self.ssh.open_sftp()

    def disconnect(self):
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def upload_file(self, local_path, remote_path):
        self.sftp.put(local_path, remote_path)

    def mkdir(self, path):
        try:
            self.sftp.mkdir(path)
        except IOError:
            # Directory already exists
            pass

    def chdir(self, path):
        self.sftp.chdir(path)

    def delete_file(self, path):
        self.sftp.remove(path)

    def list_files(self, path):
        return self.sftp.listdir(path)
