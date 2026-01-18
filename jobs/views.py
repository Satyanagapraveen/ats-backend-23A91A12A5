from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Job
from .serializers import JobSerializer, JobCreateSerializer


class JobListCreateView(APIView):
    """
    GET: List all open jobs (public for candidates)
    POST: Create a new job (recruiters only)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all open jobs"""
        user = request.user
        
        if user.role == 'candidate':
            # Candidates see only open jobs
            jobs = Job.objects.filter(status='open')
        elif user.role in ['recruiter', 'hiring_manager']:
            # Recruiters/Hiring Managers see their company's jobs
            jobs = Job.objects.filter(company=user.company)
        else:
            jobs = Job.objects.none()
        
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new job (recruiters only)"""
        user = request.user
        
        if user.role != 'recruiter':
            return Response(
                {"detail": "Only recruiters can create jobs"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not user.company:
            return Response(
                {"detail": "Recruiter must be associated with a company"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = JobCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        job = Job.objects.create(
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            status=serializer.validated_data.get('status', 'open'),
            company=user.company,
            created_by=user
        )
        
        return Response(
            JobSerializer(job).data,
            status=status.HTTP_201_CREATED
        )


class JobDetailView(APIView):
    """
    GET: Retrieve a job
    PUT: Update a job (recruiters only, own company)
    DELETE: Delete a job (recruiters only, own company)
    """
    permission_classes = [IsAuthenticated]

    def get_job(self, job_id):
        try:
            return Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return None

    def get(self, request, job_id):
        """Retrieve job details"""
        job = self.get_job(job_id)
        if not job:
            return Response(
                {"detail": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = JobSerializer(job)
        return Response(serializer.data)

    def put(self, request, job_id):
        """Update a job (recruiters only)"""
        user = request.user
        
        if user.role != 'recruiter':
            return Response(
                {"detail": "Only recruiters can update jobs"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        job = self.get_job(job_id)
        if not job:
            return Response(
                {"detail": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check company ownership
        if job.company != user.company:
            return Response(
                {"detail": "Not authorized to update this job"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = JobCreateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Update fields
        if 'title' in serializer.validated_data:
            job.title = serializer.validated_data['title']
        if 'description' in serializer.validated_data:
            job.description = serializer.validated_data['description']
        if 'status' in serializer.validated_data:
            job.status = serializer.validated_data['status']
        
        job.save()
        
        return Response(JobSerializer(job).data)

    def delete(self, request, job_id):
        """Delete a job (recruiters only)"""
        user = request.user
        
        if user.role != 'recruiter':
            return Response(
                {"detail": "Only recruiters can delete jobs"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        job = self.get_job(job_id)
        if not job:
            return Response(
                {"detail": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check company ownership
        if job.company != user.company:
            return Response(
                {"detail": "Not authorized to delete this job"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        job.delete()
        
        return Response(
            {"detail": "Job deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
