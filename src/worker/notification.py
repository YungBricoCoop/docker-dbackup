from abc import ABC, abstractmethod
from typing import List
import requests
import smtplib
from email.mime.text import MIMEText
from config import Notification
from loguru import logger
from data.BackupData import BackupData


# Abstract Base Class for Notification Clients
class NotificationClient(ABC):
    SUCCESS_COLOR = 0x2ECC71
    ERROR_COLOR = 0xE74C3C

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def send_message(self, backup_data: BackupData):
        pass


# Discord Notification Client
class DiscordNotificationClient(NotificationClient):
    def __init__(self, discord_webhook_url):
        self.discord_webhook_url = discord_webhook_url

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send_message(self, backup_data: BackupData):
        self._send_message(backup_data)

    def _send_message(self, backup_data: BackupData):
        color = self.SUCCESS_COLOR if backup_data.success else self.ERROR_COLOR

        embed_data = {
            "embeds": [
                {
                    "title": backup_data.status_short,
                    "color": color,
                    "fields": [
                        {
                            "name": "Status",
                            "value": backup_data.status,
                            "inline": False,
                        },
                        {
                            "name": "Database",
                            "value": backup_data.database,
                            "inline": True,
                        },
                        {
                            "name": "Host",
                            "value": f"{backup_data.host} ({backup_data.protocol})",
                            "inline": True,
                        },
                        {
                            "name": "Compression",
                            "value": "✅" if backup_data.compress else "❌",
                            "inline": False,
                        },
                        {
                            "name": "Encryption",
                            "value": "✅" if backup_data.encrypt else "❌",
                            "inline": False,
                        },
                        {
                            "name": "Duration",
                            "value": backup_data.duration_in_seconds,
                            "inline": False,
                        },
                    ],
                }
            ]
        }

        try:
            response = requests.post(self.discord_webhook_url, json=embed_data)
            response.raise_for_status()
            logger.debug("Notification sent successfully!")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord notification: {e}")


# Email Notification Client
class EmailNotificationClient(NotificationClient):
    def __init__(
        self,
        smtp_server,
        smtp_port,
        smtp_user,
        smtp_password,
        smtp_use_tls,
        smtp_use_ssl,
        smtp_sender,
        smtp_recipients,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
        self.smtp_use_ssl = smtp_use_ssl
        self.sender = smtp_sender
        self.recipients = smtp_recipients
        self.server = None

    def connect(self):
        try:
            if self.smtp_use_ssl:
                self.server = smtplib.SMTP_SSL(
                    self.smtp_server, self.smtp_port, timeout=10
                )
            else:
                self.server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                if self.smtp_use_tls:
                    self.server.starttls()

            self.server.login(self.smtp_user, self.smtp_password)
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")

    def disconnect(self):
        if self.server:
            self.server.quit()
            self.server = None

    def send_message(self, backup_data: BackupData):
        subject = backup_data.status_short
        color = self.SUCCESS_COLOR if backup_data.success else self.ERROR_COLOR
        message = f"""
<table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 500px; font-family: Arial, sans-serif; border: 1px solid #cccccc;">
    <tr>
        <td style="padding: 16px; background-color: #{color:06x}; color: #ffffff; font-size: 18px; font-weight: bold;">
            {backup_data.status_short}
        </td>
    </tr>
    <tr>
        <td style="padding: 16px;">
            <p style="margin: 0;"><strong>Status:</strong> {backup_data.status}</p>
        </td>
    </tr>
    <tr>
        <td style="padding: 16px;">
            <table width="100%" style="font-family: Arial, sans-serif;">
                <tr>
                    <td style="width: 50%; padding: 8px 0;">
                        <strong>Database:</strong> {backup_data.database}
                    </td>
                    <td style="width: 50%; padding: 8px 0;">
                        <strong>Host:</strong> {backup_data.host} ({backup_data.protocol})
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding: 16px;">
            <p style="margin: 0;"><strong>Compression:</strong> {"✅" if backup_data.compress else "❌"}</p>
        </td>
    </tr>
    <tr>
        <td style="padding: 16px;">
            <p style="margin: 0;"><strong>Encryption:</strong> {"✅" if backup_data.encrypt else "❌"}</p>
        </td>
    </tr>
    <tr>
        <td style="padding: 16px;">
            <p style="margin: 0;"><strong>Duration:</strong> {backup_data.duration_in_seconds} seconds</p>
        </td>
    </tr>
</table>
"""
        self._send_email(subject, message)

    def _send_email(self, subject, body):
        if not self.server:
            logger.error("SMTP server connection is not established")
            return

        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        try:
            self.server.sendmail(self.sender, self.recipients, msg.as_string())
            logger.debug("Email sent successfully to: {self.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


def send_notifications(
    backup_data: BackupData,
    notifications: List[Notification],
    notify_on_success: bool,
    notify_on_fail: bool,
):
    if (not notify_on_success and backup_data.success) or (
        not notify_on_fail and not backup_data.success
    ):
        return
    for notification in notifications:
        if notification.method == "discord":
            client = DiscordNotificationClient(notification.discord_webhook_url)
        elif notification.method == "email":
            client = EmailNotificationClient(
                notification.smtp_server,
                notification.smtp_port,
                notification.smtp_user,
                notification.smtp_password,
                notification.smtp_use_tls,
                notification.smtp_use_ssl,
                notification.smtp_sender,
                notification.smtp_recipients,
            )
        else:
            logger.error(f"Unsupported notification method: {notification.method}")
            continue

        client.connect()
        client.send_message(backup_data)
        client.disconnect()
