from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import User
from companies.models import Company


class UserModelTests(TestCase):
    """Test cases for the User model"""

    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(name="Test Company")

    def test_create_candidate_user(self):
        """Test creating a candidate user"""
        user = User.objects.create_user(
            username="candidate",
            email="candidate@test.com",
            password="testpass123",
            role="candidate"
        )
        
        self.assertEqual(user.username, "candidate")
        self.assertEqual(user.email, "candidate@test.com")
        self.assertEqual(user.role, "candidate")
        self.assertIsNone(user.company)
        self.assertTrue(user.check_password("testpass123"))

    def test_create_recruiter_user(self):
        """Test creating a recruiter user with company"""
        user = User.objects.create_user(
            username="recruiter",
            email="recruiter@test.com",
            password="testpass123",
            role="recruiter",
            company=self.company
        )
        
        self.assertEqual(user.role, "recruiter")
        self.assertEqual(user.company, self.company)

    def test_create_hiring_manager_user(self):
        """Test creating a hiring manager user"""
        user = User.objects.create_user(
            username="hiring_manager",
            email="hm@test.com",
            password="testpass123",
            role="hiring_manager",
            company=self.company
        )
        
        self.assertEqual(user.role, "hiring_manager")

    def test_user_str_representation(self):
        """Test the string representation of User"""
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            role="candidate"
        )
        
        self.assertEqual(str(user), "testuser")


class RegistrationAPITests(APITestCase):
    """Test cases for user registration API"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.company = Company.objects.create(name="Test Company")

    def test_register_candidate(self):
        """Test registering a new candidate"""
        data = {
            "username": "newcandidate",
            "email": "newcandidate@test.com",
            "password": "securepass123",
            "role": "candidate"
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newcandidate").exists())

    def test_register_recruiter_with_company(self):
        """Test registering a new recruiter with company"""
        data = {
            "username": "newrecruiter",
            "email": "newrecruiter@test.com",
            "password": "securepass123",
            "role": "recruiter",
            "company": self.company.id
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="newrecruiter")
        self.assertEqual(user.company, self.company)

    def test_register_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        User.objects.create_user(
            username="existing",
            email="existing@test.com",
            password="testpass123",
            role="candidate"
        )
        
        data = {
            "username": "existing",
            "email": "different@test.com",
            "password": "securepass123",
            "role": "candidate"
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_required_fields(self):
        """Test that missing required fields return errors"""
        data = {
            "username": "incomplete"
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationAPITests(APITestCase):
    """Test cases for JWT authentication"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            role="candidate"
        )

    def test_obtain_token_with_valid_credentials(self):
        """Test obtaining JWT token with valid credentials"""
        data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_obtain_token_with_invalid_credentials(self):
        """Test obtaining JWT token with invalid credentials"""
        data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/auth/test/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get('/api/auth/test/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
