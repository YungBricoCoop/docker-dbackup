from abc import ABC, abstractmethod
from typing import List
import requests
import smtplib
from email.mime.text import MIMEText
from config import Notification
from loguru import logger


# Abstract Base Class for Notification Clients
class NotificationClient(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def send_message(self, success, message):
        pass


# Discord Notification Client
class DiscordNotificationClient(NotificationClient):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send_message(self, success, message):
        self._send_message(message)

    def _send_message(self, content):
        data = {"content": content}
        try:
            response = requests.post(self.webhook_url, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Discord notification: {e}")


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

    def send_message(self, success, message):
        subject = "Backup Successful" if success else "Backup Failed"
        self._send_email(subject, message)

    def _send_email(self, subject, body):
        if not self.server:
            logger.error("SMTP server connection is not established")
            return

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)

        try:
            self.server.sendmail(self.sender, self.recipients, msg.as_string())
            logger.debug("Email sent successfully to: {self.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


def send_notifications(success, message, notifications: List[Notification]):
    for notification in notifications:
        if (notification.notify_on_success and success) or (
            notification.notify_on_fail and not success
        ):
            if notification.method == "discord":
                client = DiscordNotificationClient(notification.webhook_url)
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
            client.send_message(success, message)
            client.disconnect()
