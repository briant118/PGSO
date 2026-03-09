"""Utility to send emails and log them to SentEmail."""
from django.core.mail import send_mail
from django.conf import settings

from .models import SentEmail


def send_and_log_email(
    recipient_email,
    subject,
    body_plain,
    email_type=SentEmail.TYPE_OTHER,
    sent_by=None,
    related_user=None,
):
    """
    Send an email and log it to SentEmail.
    Returns True if sent successfully, False otherwise.
    """
    try:
        send_mail(
            subject=subject,
            message=body_plain,
            from_email=None,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        SentEmail.objects.create(
            recipient_email=recipient_email,
            subject=subject,
            body_plain=body_plain,
            email_type=email_type,
            sent_by=sent_by,
            related_user=related_user,
        )
        return True
    except Exception:
        return False
