from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger("checker")

@shared_task(bind=True, max_retries=3)
def send_otp_email_task(self, email: str, otp: str):
    """
    Sends an OTP email asynchronously using Celery.
    Retries up to 3 times if there is an SMTP connection error.
    """
    try:
        send_mail(
            subject='Your OSINT Data Analyzer Verification Code',
            message=(
                f'Your verification code is: {otp}\n\n'
                f'This code expires in 10 minutes.\n'
                f'Do not share this code with anyone.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {email} via Celery")
    except Exception as exc:
        logger.error(f"Failed to send OTP email to {email}: {exc}")
        # Retry the task with an exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
