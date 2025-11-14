"""
Email Client Integration
Send email notifications via SMTP
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class EmailClient:
    """SMTP Email client"""

    def __init__(self):
        self.smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = current_app.config.get('SMTP_PORT', 587)
        self.smtp_username = current_app.config.get('SMTP_USERNAME', '')
        self.smtp_password = current_app.config.get('SMTP_PASSWORD', '')
        self.smtp_from = current_app.config.get('SMTP_FROM', 'soar@company.com')
        self.smtp_use_tls = current_app.config.get('SMTP_USE_TLS', True)

        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("SMTP credentials not configured")

    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        html: bool = False,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None
    ) -> dict:
        """
        Send email

        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body
            html: Whether body is HTML
            cc_addresses: CC recipients
            bcc_addresses: BCC recipients

        Returns:
            Send result dictionary
        """
        if not all([self.smtp_username, self.smtp_password]):
            return {'error': 'SMTP not configured', 'success': False}

        try:
            # Create message
            msg = MIMEMultipart('alternative') if html else MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject

            if cc_addresses:
                msg['Cc'] = ', '.join(cc_addresses)

            # Attach body
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type))

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                server.login(self.smtp_username, self.smtp_password)

                all_recipients = to_addresses.copy()
                if cc_addresses:
                    all_recipients.extend(cc_addresses)
                if bcc_addresses:
                    all_recipients.extend(bcc_addresses)

                server.sendmail(self.smtp_from, all_recipients, msg.as_string())

            logger.info(f"Email sent to {', '.join(to_addresses)}")
            return {'success': True}

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {'error': str(e), 'success': False}

    async def send_incident_notification(
        self,
        to_addresses: List[str],
        incident_title: str,
        incident_id: int,
        severity: str,
        description: str
    ) -> dict:
        """
        Send formatted incident notification

        Args:
            to_addresses: Recipient email addresses
            incident_title: Incident title
            incident_id: Incident ID
            severity: Incident severity
            description: Incident description

        Returns:
            Send result
        """
        subject = f"[SOAR Alert - {severity.upper()}] Incident #{incident_id}: {incident_title}"

        body = f"""
        Security Incident Notification
        ================================

        Incident ID: {incident_id}
        Title: {incident_title}
        Severity: {severity.upper()}

        Description:
        {description}

        ---
        This is an automated notification from the SOAR Platform.
        Please review the incident in the dashboard.
        """

        return await self.send_email(
            to_addresses=to_addresses,
            subject=subject,
            body=body
        )
