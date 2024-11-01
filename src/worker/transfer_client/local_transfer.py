import os
import shutil

from worker.transfer_client.base import TransferClient


class LocalTransferClient(TransferClient):
    def __init__(self):
        self.current_dir = os.getcwd()

    def connect(self):
        pass

    def disconnect(self):
        pass

    def upload_file(self, local_path, remote_path):
        remote_dir, _remote_filename = os.path.split(remote_path)
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
