from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Application
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationStageUpdateSerializer,ApplicationDetailSerializer
)
from jobs.models import Job
from applications.services import change_application_stage
from notifications.tasks import send_candidate_email, send_recruiter_email


class ApplyJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1. Role check
        if user.role != 'candidate':
            return Response(
                {"detail": "Only candidates can apply for jobs"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        job_id = serializer.validated_data['job_id']
        job = Job.objects.get(id=job_id)

        # 2. Prevent duplicate applications
        if Application.objects.filter(candidate=user, job=job).exists():
            return Response(
                {"detail": "You have already applied to this job"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Create application
        application = Application.objects.create(
            candidate=user,
            job=job
        )

        send_candidate_email.delay(
        "Application Submitted",
        f"You have successfully applied for {application.job.title}",
        application.candidate.email
    )


        send_recruiter_email.delay(
    "New Job Application",
    f"A new candidate has applied for {application.job.title}",
    application.job.created_by.email
     )



        return Response(
            {
                "message": "Application submitted successfully",
                "application_id": application.id,
                "stage": application.stage
            },
            status=status.HTTP_201_CREATED
        )

# Create your views here.



class ChangeApplicationStageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, application_id):
        user = request.user

        # 1. Role check
        if user.role != 'recruiter':
            return Response(
                {"detail": "Only recruiters can change application stage"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return Response(
                {"detail": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Company check
        if application.job.company != user.company:
            return Response(
                {"detail": "You are not authorized for this application"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApplicationStageUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_stage = serializer.validated_data['new_stage']

        try:
            change_application_stage(
                application=application,
                new_stage=new_stage,
                changed_by=user
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Application stage updated",
                "new_stage": application.stage
            }
        )
class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        user = request.user

        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return Response(
                {"detail": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Candidate can view only their own application
        if user.role == 'candidate' and application.candidate != user:
            return Response(
                {"detail": "Not authorized to view this application"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Recruiter can view applications of their company
        if user.role == 'recruiter' and application.job.company != user.company:
            return Response(
                {"detail": "Not authorized to view this application"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ApplicationDetailSerializer(application)
        return Response(serializer.data)
    
class MyApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != 'candidate':
            return Response(
                {"detail": "Only candidates can view their applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        applications = Application.objects.filter(candidate=user)

        serializer = ApplicationDetailSerializer(applications, many=True)
        return Response(serializer.data)
    
class JobApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        user = request.user

        if user.role != 'recruiter':
            return Response(
                {"detail": "Only recruiters can view job applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {"detail": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if job.company != user.company:
            return Response(
                {"detail": "Not authorized to view these applications"},
                status=status.HTTP_403_FORBIDDEN
            )

        applications = Application.objects.filter(job=job)

        # Optional stage filter
        stage = request.query_params.get('stage')
        if stage:
            applications = applications.filter(stage=stage)

        serializer = ApplicationDetailSerializer(applications, many=True)
        return Response(serializer.data)

# Candidate email
