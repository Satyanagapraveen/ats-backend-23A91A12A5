from django.db import models
from django.contrib.auth.models import AbstractUser
from companies.models import Company


class User(AbstractUser):
    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('recruiter', 'Recruiter'),
        ('hiring_manager', 'Hiring Manager'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.username


# Create your models here.
