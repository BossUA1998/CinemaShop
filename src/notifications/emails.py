import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(
            self,
            smtp_server: str,
            smtp_port: int,
            smtp_user: str,
            smtp_password: str,
    ):
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password

    async def _send_email(self, to: str, subject: str, html: str):
        msg = MIMEMultipart()
        msg["From"] = self._smtp_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        try:
            async with aiosmtplib.SMTP(
                    hostname=self._smtp_server, port=self._smtp_port, start_tls=True
            ) as server:
                await server.login(self._smtp_user, self._smtp_password)
                await server.send_message(msg)
        except aiosmtplib.SMTPException:
            ...
            # TODO implement functional with error

    async def send_activation_email(self, email: str, activation_link: str, token: str):
        ...

    async def send_activation_complete_email(self, email: str):
        ...

    async def send_password_reset_email(self, email: str, password_reset_link: str):
        ...

    async def send_password_reset_complete_email(self, email: str, login_link: str):
        ...
