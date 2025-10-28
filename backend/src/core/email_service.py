"""
Email Service Module

이메일 발송 서비스 (Custom JWT Provider용)
"""
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

try:
    import aiosmtplib
    from jinja2 import Environment, FileSystemLoader
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email sending service using SMTP

    Supports:
    - Async email sending
    - HTML templates with Jinja2
    - Password reset emails
    - Email verification emails
    """

    def __init__(self):
        """Initialize email service with SMTP configuration"""
        if not EMAIL_AVAILABLE:
            logger.warning(
                "Email dependencies not installed. "
                "Install with: pip install aiosmtplib jinja2"
            )

        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

        # Jinja2 템플릿 환경 설정
        template_dir = Path(__file__).parent.parent.parent / "templates" / "email"
        if template_dir.exists():
            self.template_env = Environment(
                loader=FileSystemLoader(str(template_dir))
            )
        else:
            self.template_env = None
            logger.warning(f"Email template directory not found: {template_dir}")

    def _validate_config(self) -> bool:
        """
        Validate SMTP configuration

        Returns:
            bool: True if configuration is valid
        """
        if not EMAIL_AVAILABLE:
            logger.error("Email dependencies not installed")
            return False

        if not self.smtp_user or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False

        return True

    async def send_password_reset_email(
        self,
        email: str,
        reset_token: str,
        expires_in_minutes: int = 30
    ) -> bool:
        """
        Send password reset email

        Args:
            email: Recipient email address
            reset_token: Password reset token
            expires_in_minutes: Token expiration time in minutes

        Returns:
            bool: Success status
        """
        if not self._validate_config():
            logger.error("Email service not properly configured")
            return False

        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

            # Load and render template
            if self.template_env:
                template = self.template_env.get_template("password_reset.html")
                html_content = template.render(
                    reset_url=reset_url,
                    expires_in_minutes=expires_in_minutes
                )
            else:
                # Fallback to simple HTML
                html_content = f"""
                <html>
                <body>
                    <h2>비밀번호 재설정</h2>
                    <p>비밀번호 재설정을 요청하셨습니다.</p>
                    <p>아래 링크를 클릭하여 새 비밀번호를 설정하세요:</p>
                    <p><a href="{reset_url}">비밀번호 재설정</a></p>
                    <p>이 링크는 {expires_in_minutes}분 동안 유효합니다.</p>
                    <p>본인이 요청하지 않으셨다면 이 이메일을 무시하세요.</p>
                </body>
                </html>
                """

            success = await self._send_email(
                to_email=email,
                subject="비밀번호 재설정 요청",
                html_content=html_content
            )

            if success:
                logger.info(f"[EmailService] Password reset email sent to: {email}")
            else:
                logger.error(f"[EmailService] Failed to send password reset email to: {email}")

            return success

        except Exception as e:
            logger.error(f"[EmailService] Error sending password reset email: {e}", exc_info=True)
            return False

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)

        Returns:
            bool: Success status
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=False,
                start_tls=True
            ) as smtp:
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(message)

            logger.info(f"[EmailService] Email sent successfully to: {to_email}")
            return True

        except aiosmtplib.SMTPException as e:
            logger.error(f"[EmailService] SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"[EmailService] Error sending email: {e}", exc_info=True)
            return False


# Singleton instance
email_service = EmailService()
