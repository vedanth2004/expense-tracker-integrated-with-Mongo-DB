# notifications/email_handler.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import settings
from analytics import reports  # Ensure Reports class is imported here

class EmailHandler:
    def __init__(self, settings_obj=None):
        self.host = settings_obj.SMTP_HOST if settings_obj else settings.SMTP_HOST
        self.port = settings_obj.SMTP_PORT if settings_obj else settings.SMTP_PORT
        self.user = settings_obj.SMTP_USER if settings_obj else settings.SMTP_USER
        self.password = settings_obj.SMTP_PASS if settings_obj else settings.SMTP_PASS

    def send_test(self, to_email: str, subject: str, body: str) -> bool:
        if not (self.user and self.password and self.host):
            print("❌ Missing SMTP configuration.")
            return False

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = to_email

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, [to_email], msg.as_string())
            print("✅ Email sent successfully.")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def send_pdf_report(self, user_id: str, to_email: str, subject: str, body: str, start=None, end=None) -> bool:
        """
        Send email with PDF report attachment for given user_id between start and end dates.
        """
        try:
            # Generate PDF in memory
            pdf_bytes = reports.Reports().generate_pdf(user_id, start, end)

            # Compose email
            msg = MIMEMultipart()
            msg["From"] = self.user
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add body text
            msg.attach(MIMEText(body, "plain"))

            # Attach PDF in-memory
            msg.attach(MIMEApplication(pdf_bytes, _subtype="pdf", Name="Report.pdf"))

            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            print("✅ PDF report email sent successfully.")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
