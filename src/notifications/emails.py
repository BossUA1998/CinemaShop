import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader


class EmailSender:
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        path_to_templates: str,
        activation_email_template_name: str,
        activation_complete_email_template_name: str,
        password_email_template_name: str,
        password_complete_email_template_name: str,
        comment_answer_template_name: str,
        comment_reaction_template_name: str,
    ):
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._activation_email_template_name = activation_email_template_name
        self._activation_complete_email_template_name = (
            activation_complete_email_template_name
        )
        self._password_email_template_name = password_email_template_name
        self._password_complete_email_template_name = (
            password_complete_email_template_name
        )
        self.notification_for_comment_answer = comment_answer_template_name
        self.notification_for_comment_reaction = comment_reaction_template_name

        self._env = Environment(loader=FileSystemLoader(path_to_templates))

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

    async def send_activation_email(
        self, email: str, activation_link: str, new_activation_link: str, token: str
    ):
        template = self._env.get_template(self._activation_email_template_name)
        html = template.render(
            action_url=activation_link,
            new_action_url=new_activation_link,
            email=email,
            token=token,
        )
        subject = "Account Activation"
        await self._send_email(to=email, subject=subject, html=html)

    async def send_activation_complete_email(self, email: str, login_link: str):
        template = self._env.get_template(self._activation_complete_email_template_name)
        html = template.render(email=email, login_link=login_link)
        subject = "Account Activation"
        await self._send_email(to=email, subject=subject, html=html)

    async def send_password_reset_email(
        self, email: str, password_reset_link: str, token: str, new_password: str
    ):
        template = self._env.get_template(self._password_email_template_name)
        html = template.render(
            email=email,
            token=token,
            new_password=new_password,
            password_reset_link=password_reset_link,
        )
        subject = "Password Reset"
        await self._send_email(to=email, subject=subject, html=html)

    async def send_password_reset_complete_email(self, email: str, login_link: str):
        template = self._env.get_template(self._password_complete_email_template_name)
        html = template.render(email=email, login_link=login_link)
        subject = "Password Reset"
        await self._send_email(to=email, subject=subject, html=html)

    async def send_reply_notification_to_comment(
        self, email: str, comment: str, movie_name: str
    ):
        template = self._env.get_template(self.notification_for_comment_answer)
        html = template.render(comment=comment, movie_name=movie_name)
        subject = "Reply Notification"
        await self._send_email(to=email, subject=subject, html=html)

    async def send_notification_about_reaction_to_comment(
        self, email: str, movie_name: str
    ):
        template = self._env.get_template(self.notification_for_comment_reaction)
        html = template.render(movie_name=movie_name)
        subject = "Reaction Notification"
        await self._send_email(to=email, subject=subject, html=html)
