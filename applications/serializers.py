from rest_framework import serializers
from .models import Application
from jobs.models import Job


class ApplicationCreateSerializer(serializers.ModelSerializer):
    job_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Application
        fields = ['job_id']

    def validate_job_id(self, job_id):
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job does not exist")

        if job.status != 'open':
            raise serializers.ValidationError("Job is closed")

        return job_id

class ApplicationStageUpdateSerializer(serializers.Serializer):
    new_stage = serializers.CharField()


class ApplicationDetailSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    candidate_username = serializers.CharField(source='candidate.username', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id',
            'candidate_username',
            'job_title',
            'company_name',
            'stage',
            'applied_at',
        ]
