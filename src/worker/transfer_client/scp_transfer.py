import paramiko
from scp import SCPClient as scp_SCPClient

from worker.transfer_client.base import TransferClient


class SCPTransferClient(TransferClient):
    def __init__(self, host):
        self.host = host
        self.ssh = None

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

    def disconnect(self):
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def upload_file(self, local_path, remote_path):
        with scp_SCPClient(self.ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)

    def mkdir(self, path):
        _stdin, stdout, _stderr = self.ssh.exec_command(f"mkdir -p '{path}'")
        stdout.channel.recv_exit_status()

    def chdir(self, path):
        pass

    def delete_file(self, path):
        _stdin, stdout, _stderr = self.ssh.exec_command(f"rm '{path}'")
        stdout.channel.recv_exit_status()

    def list_files(self, path):
        _stdin, stdout, _stderr = self.ssh.exec_command(f"ls -1 '{path}'")
        stdout.channel.recv_exit_status()
        return stdout.read().decode().splitlines()
