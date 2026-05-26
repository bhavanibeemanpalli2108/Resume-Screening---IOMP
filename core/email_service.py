import os
import logging
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, Subject, PlainTextContent, HtmlContent

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

logger = logging.getLogger(__name__)


def _send(to_email: str, subject: str, plain: str, html: str, company_name: str) -> bool:
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        logger.error("SendGrid credentials not set.")
        return False
    try:
        message = Mail(
            from_email=From(SENDER_EMAIL, company_name),
            to_emails=To(to_email),
            subject=Subject(subject),
            plain_text_content=PlainTextContent(plain),
            html_content=HtmlContent(html),
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code in (200, 202):
            logger.info("Email sent to %s (status %s)", to_email, response.status_code)
            return True
        logger.error("SendGrid status %s for %s", response.status_code, to_email)
        return False
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False


def send_shortlist_email(
    to_email: str,
    job_title: str,
    feedback: str = "",
    company_name: str = "AI Recruitment System",
) -> bool:
    """Send shortlist notification with optional AI feedback."""
    subject = f"🎉 Congratulations! You've Been Shortlisted — {job_title}"
    feedback_block = f"<p><em>{feedback}</em></p>" if feedback else ""
    feedback_plain = f"\n\n{feedback}" if feedback else ""

    plain = f"""Dear Candidate,

Congratulations! You have been shortlisted for: {job_title}{feedback_plain}

Our team will reach out shortly with interview details.

Best regards,
{company_name} Recruitment Team""".strip()

    html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;padding:20px;">
  <div style="background:#2e7d32;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="color:white;margin:0;">🎉 You've Been Shortlisted!</h2>
  </div>
  <div style="background:#f9f9f9;padding:25px;border-radius:0 0 8px 8px;border:1px solid #ddd;">
    <p>Dear Candidate,</p>
    <p>Congratulations! You have been shortlisted for: <strong style="color:#2e7d32;">{job_title}</strong></p>
    {feedback_block}
    <h3 style="color:#2e7d32;">Next Steps</h3>
    <ul>
      <li>Our team will contact you shortly with interview scheduling details.</li>
      <li>Keep an eye on your inbox.</li>
    </ul>
    <p>We look forward to speaking with you!</p>
    <br><p>Best regards,<br><strong>{company_name} Recruitment Team</strong></p>
  </div>
</body></html>"""

    return _send(to_email, subject, plain, html, company_name)


def send_rejection_email(
    to_email: str,
    job_title: str,
    feedback: str = "",
    company_name: str = "AI Recruitment System",
) -> bool:
    """Send rejection notification with optional AI feedback."""
    subject = f"Your Application for {job_title} — Update"
    feedback_block = f"<p><em>{feedback}</em></p>" if feedback else ""
    feedback_plain = f"\n\n{feedback}" if feedback else ""

    plain = f"""Dear Candidate,

Thank you for applying for: {job_title}

After careful review, we regret to inform you that your application has not been taken forward at this time.{feedback_plain}

We encourage you to keep developing your skills and apply for future opportunities.

Best regards,
{company_name} Recruitment Team""".strip()

    html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;padding:20px;">
  <div style="background:#c62828;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="color:white;margin:0;">Application Update — {job_title}</h2>
  </div>
  <div style="background:#f9f9f9;padding:25px;border-radius:0 0 8px 8px;border:1px solid #ddd;">
    <p>Dear Candidate,</p>
    <p>Thank you for applying for <strong>{job_title}</strong>.</p>
    <p>After careful review, we regret to inform you that your application has not been taken forward at this time.</p>
    {feedback_block}
    <p>We encourage you to keep developing your skills and apply for future opportunities with us.</p>
    <br><p>Best regards,<br><strong>{company_name} Recruitment Team</strong></p>
  </div>
</body></html>"""

    return _send(to_email, subject, plain, html, company_name)


def send_ats_feedback_email(
    to_email: str,
    job_title: str,
    ats_score: float,
    feedback: str,
    company_name: str = "AI Recruitment System",
) -> bool:
    """Send ATS score + AI feedback to candidate after they apply."""
    pct = round(ats_score * 100, 1)
    subject = f"Your ATS Score for {job_title} — {pct}%"

    plain = f"""Dear Candidate,

Here is your ATS analysis for: {job_title}
ATS Match Score: {pct}%

{feedback}

Best regards,
{company_name} Recruitment Team""".strip()

    html = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto;padding:20px;">
  <div style="background:#0a66c2;padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="color:white;margin:0;">📊 Your ATS Score: {pct}%</h2>
  </div>
  <div style="background:#f9f9f9;padding:25px;border-radius:0 0 8px 8px;border:1px solid #ddd;">
    <p>Dear Candidate,</p>
    <p>Here is your ATS analysis for <strong>{job_title}</strong>:</p>
    <div style="background:#e8f5e9;border-left:4px solid #2e7d32;padding:12px;margin:15px 0;border-radius:4px;">
      <strong>ATS Match Score: {pct}%</strong>
    </div>
    <p><em>{feedback}</em></p>
    <br><p>Best regards,<br><strong>{company_name} Recruitment Team</strong></p>
  </div>
</body></html>"""

    return _send(to_email, subject, plain, html, company_name)
