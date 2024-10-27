from datetime import datetime


class BackupData:
    def __init__(
        self,
        id: str,
        database: str,
        host: str,
        protocol: str,
        compress: bool,
        encrypt: bool,
    ):
        self.id = id
        self.database = database
        self.host = host
        self.protocol = protocol
        self.compress = compress
        self.encrypt = encrypt
        self.success = False
        self.status_short = None
        self.status = None
        self.error = None
        self.start_time = datetime.now()
        self.end_time = None
        self.duration_in_seconds = None

    def _get_backup_data_succes_status(self) -> str:
        return f"[{self.id}] Backup task completed successfully!"

    def _get_backup_data_fail_status(self, error: str) -> str:
        return f"[{self.id}] Backup task failed: {error}"

    def set_status(self, success, error=None):
        self.status_short = (
            f"✅ Backup [{self.id}] successful ✅"
            if success
            else f"❌ Backup [{self.id}] failed ❌"
        )
        self.status = "Operational" if success else f"Error - {error}"
        self.success = success
        self.error = error
        self.end_time = datetime.now()
        self.duration_in_seconds = (
            f"{round((self.end_time - self.start_time).total_seconds(), 3)}s"
        )
