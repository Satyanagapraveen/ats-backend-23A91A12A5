from django.db import models
from jobs.models import Job
from accounts.models import User


class Application(models.Model):
    STAGE_CHOICES = (
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
    )

    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default='applied'
    )

    applied_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"

class ApplicationHistory(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='history'
    )

    from_stage = models.CharField(max_length=20)
    to_stage = models.CharField(max_length=20)

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} : {self.from_stage} → {self.to_stage}"
