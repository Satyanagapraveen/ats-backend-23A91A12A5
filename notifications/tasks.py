from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def send_candidate_email(self, subject, message, email):
    """
    Sends email to candidate asynchronously
    """
    try:
        print(f"[CELERY] Sending candidate email to: {email}")
        logger.info(f"Sending candidate email to {email}")

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        print(f"[CELERY] Candidate email SENT to: {email}")
        logger.info(f"Candidate email sent to {email}")

    except Exception as e:
        print(f"[CELERY ERROR] Candidate email failed: {e}")
        logger.error(f"Candidate email failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={"max_retries": 3})
def send_recruiter_email(self, subject, message, email):
    """
    Sends email to recruiter asynchronously
    """
    try:
        print(f"[CELERY] Sending recruiter email to: {email}")
        logger.info(f"Sending recruiter email to {email}")

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        print(f"[CELERY] Recruiter email SENT to: {email}")
        logger.info(f"Recruiter email sent to {email}")

    except Exception as e:
        print(f"[CELERY ERROR] Recruiter email failed: {e}")
        logger.error(f"Recruiter email failed: {e}")
        raise self.retry(exc=e)
