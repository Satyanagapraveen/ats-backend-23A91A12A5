import pytest
from rest_framework.test import APIClient

from accounts.models import User
from companies.models import Company


@pytest.fixture
def api_client():
    """Return an API client for testing"""
    return APIClient()


@pytest.fixture
def company(db):
    """Create and return a test company"""
    return Company.objects.create(name="Test Company")


@pytest.fixture
def candidate(db):
    """Create and return a test candidate user"""
    return User.objects.create_user(
        username="test_candidate",
        email="candidate@test.com",
        password="testpass123",
        role="candidate"
    )


@pytest.fixture
def recruiter(db, company):
    """Create and return a test recruiter user"""
    return User.objects.create_user(
        username="test_recruiter",
        email="recruiter@test.com",
        password="testpass123",
        role="recruiter",
        company=company
    )


@pytest.fixture
def authenticated_candidate_client(api_client, candidate):
    """Return an API client authenticated as a candidate"""
    api_client.force_authenticate(user=candidate)
    return api_client


@pytest.fixture
def authenticated_recruiter_client(api_client, recruiter):
    """Return an API client authenticated as a recruiter"""
    api_client.force_authenticate(user=recruiter)
    return api_client
