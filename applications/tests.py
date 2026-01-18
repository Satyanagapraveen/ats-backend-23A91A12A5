from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch

from accounts.models import User
from companies.models import Company
from jobs.models import Job
from applications.models import Application, ApplicationHistory
from applications.services import change_application_stage, VALID_TRANSITIONS


class StateMachineTests(TestCase):
    """Test cases for the application state machine logic"""

    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(name="Test Company")
        
        self.recruiter = User.objects.create_user(
            username="recruiter",
            email="recruiter@test.com",
            password="testpass123",
            role="recruiter",
            company=self.company
        )
        
        self.candidate = User.objects.create_user(
            username="candidate",
            email="candidate@test.com",
            password="testpass123",
            role="candidate"
        )
        
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Test job description",
            status="open",
            company=self.company,
            created_by=self.recruiter
        )
        
        self.application = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            stage="applied"
        )

    def test_valid_transitions_structure(self):
        """Test that VALID_TRANSITIONS has all required stages"""
        expected_stages = ['applied', 'screening', 'interview', 'offer', 'hired', 'rejected']
        for stage in expected_stages:
            self.assertIn(stage, VALID_TRANSITIONS)

    @patch('applications.services.send_candidate_email.delay')
    def test_valid_transition_applied_to_screening(self, mock_email):
        """Test valid transition from applied to screening"""
        change_application_stage(self.application, 'screening', self.recruiter)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, 'screening')

    @patch('applications.services.send_candidate_email.delay')
    def test_valid_transition_applied_to_rejected(self, mock_email):
        """Test valid transition from applied to rejected"""
        change_application_stage(self.application, 'rejected', self.recruiter)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, 'rejected')

    @patch('applications.services.send_candidate_email.delay')
    def test_valid_transition_screening_to_interview(self, mock_email):
        """Test valid transition from screening to interview"""
        self.application.stage = 'screening'
        self.application.save()
        
        change_application_stage(self.application, 'interview', self.recruiter)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, 'interview')

    @patch('applications.services.send_candidate_email.delay')
    def test_valid_transition_interview_to_offer(self, mock_email):
        """Test valid transition from interview to offer"""
        self.application.stage = 'interview'
        self.application.save()
        
        change_application_stage(self.application, 'offer', self.recruiter)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, 'offer')

    @patch('applications.services.send_candidate_email.delay')
    def test_valid_transition_offer_to_hired(self, mock_email):
        """Test valid transition from offer to hired"""
        self.application.stage = 'offer'
        self.application.save()
        
        change_application_stage(self.application, 'hired', self.recruiter)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, 'hired')

    def test_invalid_transition_applied_to_interview(self):
        """Test invalid transition from applied directly to interview"""
        with self.assertRaises(ValueError) as context:
            change_application_stage(self.application, 'interview', self.recruiter)
        
        self.assertIn('Invalid stage transition', str(context.exception))
        
        # Ensure stage didn't change
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, 'applied')

    def test_invalid_transition_applied_to_offer(self):
        """Test invalid transition from applied directly to offer"""
        with self.assertRaises(ValueError):
            change_application_stage(self.application, 'offer', self.recruiter)

    def test_invalid_transition_applied_to_hired(self):
        """Test invalid transition from applied directly to hired"""
        with self.assertRaises(ValueError):
            change_application_stage(self.application, 'hired', self.recruiter)

    def test_invalid_transition_from_hired(self):
        """Test that hired is a terminal state"""
        self.application.stage = 'hired'
        self.application.save()
        
        with self.assertRaises(ValueError):
            change_application_stage(self.application, 'rejected', self.recruiter)

    def test_invalid_transition_from_rejected(self):
        """Test that rejected is a terminal state"""
        self.application.stage = 'rejected'
        self.application.save()
        
        with self.assertRaises(ValueError):
            change_application_stage(self.application, 'screening', self.recruiter)

    @patch('applications.services.send_candidate_email.delay')
    def test_audit_log_created_on_transition(self, mock_email):
        """Test that ApplicationHistory is created on valid transition"""
        initial_history_count = ApplicationHistory.objects.filter(
            application=self.application
        ).count()
        
        change_application_stage(self.application, 'screening', self.recruiter)
        
        new_history_count = ApplicationHistory.objects.filter(
            application=self.application
        ).count()
        
        self.assertEqual(new_history_count, initial_history_count + 1)
        
        # Verify history details
        history = ApplicationHistory.objects.filter(
            application=self.application
        ).latest('changed_at')
        
        self.assertEqual(history.from_stage, 'applied')
        self.assertEqual(history.to_stage, 'screening')
        self.assertEqual(history.changed_by, self.recruiter)

    def test_audit_log_not_created_on_invalid_transition(self):
        """Test that ApplicationHistory is NOT created on invalid transition"""
        initial_history_count = ApplicationHistory.objects.filter(
            application=self.application
        ).count()
        
        with self.assertRaises(ValueError):
            change_application_stage(self.application, 'hired', self.recruiter)
        
        new_history_count = ApplicationHistory.objects.filter(
            application=self.application
        ).count()
        
        self.assertEqual(new_history_count, initial_history_count)

    @patch('applications.services.send_candidate_email.delay')
    def test_email_sent_on_valid_transition(self, mock_email):
        """Test that email is sent on valid transition"""
        change_application_stage(self.application, 'screening', self.recruiter)
        
        mock_email.assert_called_once()
        call_args = mock_email.call_args[0]
        self.assertIn('Application Status Update', call_args[0])
        self.assertEqual(call_args[2], self.candidate.email)


class ApplicationAPITests(APITestCase):
    """Test cases for application API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.company = Company.objects.create(name="Test Company")
        self.other_company = Company.objects.create(name="Other Company")
        
        self.recruiter = User.objects.create_user(
            username="recruiter",
            email="recruiter@test.com",
            password="testpass123",
            role="recruiter",
            company=self.company
        )
        
        self.other_recruiter = User.objects.create_user(
            username="other_recruiter",
            email="other_recruiter@test.com",
            password="testpass123",
            role="recruiter",
            company=self.other_company
        )
        
        self.candidate = User.objects.create_user(
            username="candidate",
            email="candidate@test.com",
            password="testpass123",
            role="candidate"
        )
        
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Test job description",
            status="open",
            company=self.company,
            created_by=self.recruiter
        )
        
        self.closed_job = Job.objects.create(
            title="Closed Position",
            description="This job is closed",
            status="closed",
            company=self.company,
            created_by=self.recruiter
        )

    @patch('applications.views.send_candidate_email.delay')
    @patch('applications.views.send_recruiter_email.delay')
    def test_candidate_can_apply_for_job(self, mock_recruiter_email, mock_candidate_email):
        """Test that a candidate can apply for an open job"""
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.post('/api/applications/apply/', {'job_id': self.job.id})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('application_id', response.data)
        self.assertEqual(response.data['stage'], 'applied')

    def test_recruiter_cannot_apply_for_job(self):
        """Test that a recruiter cannot apply for jobs"""
        self.client.force_authenticate(user=self.recruiter)
        
        response = self.client.post('/api/applications/apply/', {'job_id': self.job.id})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('applications.views.send_candidate_email.delay')
    @patch('applications.views.send_recruiter_email.delay')
    def test_candidate_cannot_apply_twice(self, mock_recruiter_email, mock_candidate_email):
        """Test that a candidate cannot apply to the same job twice"""
        self.client.force_authenticate(user=self.candidate)
        
        # First application
        self.client.post('/api/applications/apply/', {'job_id': self.job.id})
        
        # Second application attempt
        response = self.client.post('/api/applications/apply/', {'job_id': self.job.id})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already applied', response.data['detail'].lower())

    def test_candidate_cannot_apply_for_closed_job(self):
        """Test that a candidate cannot apply for a closed job"""
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.post('/api/applications/apply/', {'job_id': self.closed_job.id})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_cannot_apply(self):
        """Test that unauthenticated users cannot apply for jobs"""
        response = self.client.post('/api/applications/apply/', {'job_id': self.job.id})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('applications.views.send_candidate_email.delay')
    @patch('applications.views.send_recruiter_email.delay')
    @patch('applications.services.send_candidate_email.delay')
    def test_recruiter_can_change_application_stage(
        self, mock_service_email, mock_recruiter_email, mock_candidate_email
    ):
        """Test that a recruiter can change application stage"""
        # Create application first
        application = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            stage='applied'
        )
        
        self.client.force_authenticate(user=self.recruiter)
        
        response = self.client.post(
            f'/api/applications/{application.id}/change-stage/',
            {'new_stage': 'screening'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        application.refresh_from_db()
        self.assertEqual(application.stage, 'screening')

    def test_candidate_cannot_change_application_stage(self):
        """Test that a candidate cannot change application stage"""
        application = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            stage='applied'
        )
        
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.post(
            f'/api/applications/{application.id}/change-stage/',
            {'new_stage': 'screening'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_cannot_change_other_company_application(self):
        """Test that a recruiter cannot change applications from other companies"""
        application = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            stage='applied'
        )
        
        # Authenticate as recruiter from different company
        self.client.force_authenticate(user=self.other_recruiter)
        
        response = self.client.post(
            f'/api/applications/{application.id}/change-stage/',
            {'new_stage': 'screening'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ApplicationModelTests(TestCase):
    """Test cases for Application model"""

    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(name="Test Company")
        
        self.recruiter = User.objects.create_user(
            username="recruiter",
            email="recruiter@test.com",
            password="testpass123",
            role="recruiter",
            company=self.company
        )
        
        self.candidate = User.objects.create_user(
            username="candidate",
            email="candidate@test.com",
            password="testpass123",
            role="candidate"
        )
        
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Test job description",
            status="open",
            company=self.company,
            created_by=self.recruiter
        )

    def test_application_default_stage(self):
        """Test that new applications default to 'applied' stage"""
        application = Application.objects.create(
            candidate=self.candidate,
            job=self.job
        )
        
        self.assertEqual(application.stage, 'applied')

    def test_application_str_representation(self):
        """Test the string representation of Application"""
        application = Application.objects.create(
            candidate=self.candidate,
            job=self.job
        )
        
        expected_str = f"{self.candidate.username} - {self.job.title}"
        self.assertEqual(str(application), expected_str)

    def test_application_history_str_representation(self):
        """Test the string representation of ApplicationHistory"""
        application = Application.objects.create(
            candidate=self.candidate,
            job=self.job
        )
        
        history = ApplicationHistory.objects.create(
            application=application,
            from_stage='applied',
            to_stage='screening',
            changed_by=self.recruiter
        )
        
        self.assertIn('applied', str(history))
        self.assertIn('screening', str(history))
