from abc import ABC, abstractmethod


class TransferClient(ABC):
    DEFAULT_TIMEOUT_IN_SECONDS = 10

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
