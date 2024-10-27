import os
import shutil
from abc import ABC, abstractmethod
from ftplib import FTP, error_perm

import paramiko
from loguru import logger
from scp import SCPClient as scp_SCPClient

from worker.file import get_backups_to_delete, get_filename_from_path

DEFAULT_TIMEOUT_IN_SECONDS = 10


class BackupClient(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def upload_file(self, local_path, remote_path):
        pass

    @abstractmethod
    def mkdir(self, path):
        pass

    @abstractmethod
    def chdir(self, path):
        pass

    @abstractmethod
    def delete_file(self, path):
        pass

    @abstractmethod
    def list_files(self, path):
        pass


class SCPBackupClient(BackupClient):
    def __init__(self, host):
        self.host = host
        self.ssh = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.host.password:
            self.ssh.connect(
                hostname=self.host.host,
                port=self.host.port,
                username=self.host.username,
                password=self.host.password,
                timeout=DEFAULT_TIMEOUT_IN_SECONDS,
            )
        elif self.host.private_ssh_key:
            self.ssh.connect(
                hostname=self.host.host,
                port=self.host.port,
                username=self.host.username,
                key_filename=self.host.private_ssh_key,
                timeout=DEFAULT_TIMEOUT_IN_SECONDS,
            )

    def disconnect(self):
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def upload_file(self, local_path, remote_path):
        with scp_SCPClient(self.ssh.get_transport()) as scp:
            scp.put(local_path, remote_path)

    def mkdir(self, path):
        stdin, stdout, stderr = self.ssh.exec_command(f"mkdir -p '{path}'")
        stdout.channel.recv_exit_status()

    def chdir(self, path):
        pass

    def delete_file(self, path):
        stdin, stdout, stderr = self.ssh.exec_command(f"rm '{path}'")
        stdout.channel.recv_exit_status()

    def list_files(self, path):
        stdin, stdout, stderr = self.ssh.exec_command(f"ls -1 '{path}'")
        stdout.channel.recv_exit_status()
        return stdout.read().decode().splitlines()


# SFTP implementation
class SFTPBackupClient(BackupClient):
    def __init__(self, host):
        self.host = host
        self.ssh = None
        self.sftp = None

    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.host.password:
            self.ssh.connect(
                hostname=self.host.host,
                port=self.host.port,
                username=self.host.username,
                password=self.host.password,
                timeout=DEFAULT_TIMEOUT_IN_SECONDS,
            )
        elif self.host.private_ssh_key:
            self.ssh.connect(
                hostname=self.host.host,
                port=self.host.port,
                username=self.host.username,
                key_filename=self.host.private_ssh_key,
                timeout=DEFAULT_TIMEOUT_IN_SECONDS,
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


# FTP implementation
class FTPBackupClient(BackupClient):
    def __init__(self, host):
        self.host = host
        self.ftp = None

    def connect(self):
        self.ftp = FTP()
        self.ftp.connect(
            self.host.host, self.host.port, timeout=DEFAULT_TIMEOUT_IN_SECONDS
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
        for dir in dirs:
            current_dir += f"/{dir}"
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


class LocalBackupClient(BackupClient):
    def __init__(self):
        self.current_dir = os.getcwd()

    def connect(self):
        pass

    def disconnect(self):
        pass

    def upload_file(self, local_path, remote_path):
        remote_dir, remote_filename = os.path.split(remote_path)
        self.mkdir(remote_dir)
        shutil.copy2(local_path, remote_path)

    def mkdir(self, path):
        os.makedirs(path, exist_ok=True)

    def chdir(self, path):
        os.chdir(path)
        self.current_dir = path

    def delete_file(self, path):
        os.remove(path)

    def list_files(self, path):
        return os.listdir(path)


def get_client(type: str, host=None):
    if type == "scp":
        return SCPBackupClient(host)
    elif type == "sftp":
        return SFTPBackupClient(host)
    elif type == "ftp":
        return FTPBackupClient(host)
    elif type == "local":
        return LocalBackupClient()
    else:
        raise ValueError(f"Unknown type: {type}")


def upload_backup(
    type: str,
    local_filepath: str,
    remote_dir_path: str,
    host,
):
    client = get_client(type, host)
    client.connect()
    try:
        client.mkdir(remote_dir_path)
        remote_filename = get_filename_from_path(local_filepath)
        remote_filepath = os.path.join(remote_dir_path, remote_filename)
        client.upload_file(local_filepath, remote_filepath)
        logger.info(f"File sent successfully to {remote_filepath}")
    except Exception as e:
        logger.error(f"Failed to send file: {e}")
        raise
    finally:
        client.disconnect()


def remove_old_backups(
    type: str,
    remote_dir_path: str,
    filename_prefix: str,
    date_format: str,
    max_backup_files: int,
    host,
):
    client = get_client(type, host)
    client.connect()
    try:
        files = client.list_files(remote_dir_path)
        files_to_delete = get_backups_to_delete(
            files, filename_prefix, date_format, max_backup_files
        )
        if not files_to_delete:
            return
        for file in files_to_delete:
            remote_file_path = os.path.join(remote_dir_path, file)
            client.delete_file(remote_file_path)
            logger.info(f"Deleted old backup file: {remote_file_path}")
    except Exception as e:
        logger.error(f"Failed to remove old backups: {e}")
        raise
    finally:
        client.disconnect()
