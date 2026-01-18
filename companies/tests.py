from django.test import TestCase

from companies.models import Company


class CompanyModelTests(TestCase):
    """Test cases for the Company model"""

    def test_create_company(self):
        """Test creating a company"""
        company = Company.objects.create(name="Acme Corp")
        
        self.assertEqual(company.name, "Acme Corp")
        self.assertIsNotNone(company.created_at)

    def test_company_str_representation(self):
        """Test the string representation of Company"""
        company = Company.objects.create(name="Tech Startup")
        
        self.assertEqual(str(company), "Tech Startup")

    def test_multiple_companies(self):
        """Test creating multiple companies"""
        company1 = Company.objects.create(name="Company One")
        company2 = Company.objects.create(name="Company Two")
        
        self.assertEqual(Company.objects.count(), 2)
        self.assertNotEqual(company1.id, company2.id)
