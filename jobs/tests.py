from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import User
from companies.models import Company
from jobs.models import Job


class JobModelTests(TestCase):
    """Test cases for the Job model"""

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

    def test_create_job(self):
        """Test creating a job"""
        job = Job.objects.create(
            title="Software Engineer",
            description="Build great software",
            company=self.company,
            created_by=self.recruiter
        )
        
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.status, "open")  # Default status
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.created_by, self.recruiter)

    def test_job_default_status(self):
        """Test that new jobs default to 'open' status"""
        job = Job.objects.create(
            title="Test Job",
            description="Test description",
            company=self.company,
            created_by=self.recruiter
        )
        
        self.assertEqual(job.status, "open")

    def test_job_str_representation(self):
        """Test the string representation of Job"""
        job = Job.objects.create(
            title="Backend Developer",
            description="Build APIs",
            company=self.company,
            created_by=self.recruiter
        )
        
        self.assertEqual(str(job), "Backend Developer")

    def test_job_can_be_closed(self):
        """Test that a job can be set to closed status"""
        job = Job.objects.create(
            title="Position to Close",
            description="This will be closed",
            company=self.company,
            created_by=self.recruiter
        )
        
        job.status = "closed"
        job.save()
        
        job.refresh_from_db()
        self.assertEqual(job.status, "closed")

    def test_job_company_relationship(self):
        """Test the job-company relationship"""
        job = Job.objects.create(
            title="Test Job",
            description="Test",
            company=self.company,
            created_by=self.recruiter
        )
        
        # Access jobs from company
        self.assertIn(job, self.company.jobs.all())

    def test_job_created_by_relationship(self):
        """Test the job-user relationship"""
        job = Job.objects.create(
            title="Test Job",
            description="Test",
            company=self.company,
            created_by=self.recruiter
        )
        
        # Access created jobs from user
        self.assertIn(job, self.recruiter.created_jobs.all())


class JobAPITests(APITestCase):
    """Test cases for Job API endpoints"""

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
            email="other@test.com",
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
        
        self.hiring_manager = User.objects.create_user(
            username="hiring_manager",
            email="hm@test.com",
            password="testpass123",
            role="hiring_manager",
            company=self.company
        )
        
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Build software",
            company=self.company,
            created_by=self.recruiter
        )

    def test_recruiter_can_create_job(self):
        """Test that a recruiter can create a job"""
        self.client.force_authenticate(user=self.recruiter)
        
        response = self.client.post('/api/jobs/', {
            'title': 'New Job',
            'description': 'New job description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Job')
        self.assertEqual(response.data['company'], self.company.id)

    def test_candidate_cannot_create_job(self):
        """Test that a candidate cannot create a job"""
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.post('/api/jobs/', {
            'title': 'New Job',
            'description': 'New job description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_can_update_own_company_job(self):
        """Test that a recruiter can update their company's job"""
        self.client.force_authenticate(user=self.recruiter)
        
        response = self.client.put(f'/api/jobs/{self.job.id}/', {
            'title': 'Updated Title',
            'description': 'Updated description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_recruiter_cannot_update_other_company_job(self):
        """Test that a recruiter cannot update another company's job"""
        self.client.force_authenticate(user=self.other_recruiter)
        
        response = self.client.put(f'/api/jobs/{self.job.id}/', {
            'title': 'Hacked Title'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_can_delete_own_company_job(self):
        """Test that a recruiter can delete their company's job"""
        self.client.force_authenticate(user=self.recruiter)
        
        response = self.client.delete(f'/api/jobs/{self.job.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_recruiter_cannot_delete_other_company_job(self):
        """Test that a recruiter cannot delete another company's job"""
        self.client.force_authenticate(user=self.other_recruiter)
        
        response = self.client.delete(f'/api/jobs/{self.job.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_candidate_sees_only_open_jobs(self):
        """Test that candidates only see open jobs"""
        # Create a closed job
        Job.objects.create(
            title="Closed Position",
            description="This is closed",
            status="closed",
            company=self.company,
            created_by=self.recruiter
        )
        
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.get('/api/jobs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see the one open job
        for job in response.data:
            self.assertEqual(job['status'], 'open')

    def test_recruiter_sees_own_company_jobs(self):
        """Test that recruiters see their company's jobs"""
        self.client.force_authenticate(user=self.recruiter)
        
        response = self.client.get('/api/jobs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for job in response.data:
            self.assertEqual(job['company'], self.company.id)

    def test_hiring_manager_sees_own_company_jobs(self):
        """Test that hiring managers see their company's jobs"""
        self.client.force_authenticate(user=self.hiring_manager)
        
        response = self.client.get('/api/jobs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for job in response.data:
            self.assertEqual(job['company'], self.company.id)
