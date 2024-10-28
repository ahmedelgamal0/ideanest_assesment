# tasks.py
import os

from celery import Celery
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ideanest_assesment.settings import settings

app = Celery(__name__)
app.conf.broker_url = str(settings.redis_url)
app.conf.result_backend = str(settings.redis_url)

SENDGRID_API_KEY = settings.sendgrid_api_key


@app.task(name="send_invitation_email")
def send_invitation_email(
    organization_name: str, invited_user_email: str, inviter_email: str
) -> None:
    """Sends an invitation email to the invited user."""
    message = Mail(
        from_email=inviter_email,  # Use the inviter's email as the sender
        to_emails=invited_user_email,
        subject=f"Invitation to join {organization_name} on Ideanest",
        html_content=f"""
            <p>Hi,</p>
            <p>You have been invited by {inviter_email} to join the 
               organization <strong>{organization_name}</strong> on Ideanest.</p>
            <p>Click here to accept the invitation:</p>
            <a href="#">Accept Invitation</a>
            <p>(This is a placeholder link. You'll need to implement the invitation acceptance logic.)</p>
            <p>Best regards,</p>
            <p>The Ideanest Team</p>
        """,  # noqa: E501
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {invited_user_email}:", response.status_code)
    except Exception as e:
        print(f"Error sending email to {invited_user_email}:", e)

