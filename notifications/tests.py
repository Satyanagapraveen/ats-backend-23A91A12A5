from django.test import TestCase
from unittest.mock import patch, MagicMock

from notifications.tasks import send_candidate_email, send_recruiter_email


class CeleryTaskTests(TestCase):
    """Test cases for Celery notification tasks"""

    def test_send_candidate_email_task(self):
        """Test send_candidate_email task execution"""
        with patch('notifications.tasks.logger') as mock_logger:
            result = send_candidate_email(
                "Test Subject",
                "Test Message",
                "candidate@test.com"
            )
            
            # Verify logger was called
            mock_logger.info.assert_called()

    def test_send_recruiter_email_task(self):
        """Test send_recruiter_email task execution"""
        with patch('notifications.tasks.logger') as mock_logger:
            result = send_recruiter_email(
                "Test Subject",
                "Test Message",
                "recruiter@test.com"
            )
            
            # Verify logger was called
            mock_logger.info.assert_called()

    def test_send_candidate_email_with_unicode(self):
        """Test send_candidate_email handles unicode characters"""
        with patch('notifications.tasks.logger'):
            # Should not raise any exceptions
            result = send_candidate_email(
                "Application Update 📧",
                "Your application has been updated ✅",
                "candidate@test.com"
            )

    def test_send_recruiter_email_with_unicode(self):
        """Test send_recruiter_email handles unicode characters"""
        with patch('notifications.tasks.logger'):
            # Should not raise any exceptions
            result = send_recruiter_email(
                "New Application 📬",
                "A new candidate has applied ✨",
                "recruiter@test.com"
            )
