from django.urls import path
from .views import ApplyJobView
from .views import ApplyJobView, ChangeApplicationStageView, ApplicationDetailView,MyApplicationsView,JobApplicationsView
 
urlpatterns = [
    path('apply/', ApplyJobView.as_view(), name='apply-job'),
    path('<int:application_id>/change-stage/', ChangeApplicationStageView.as_view()),
    path('<int:application_id>/', ApplicationDetailView.as_view()),
    path('my/', MyApplicationsView.as_view()),
    path('job/<int:job_id>/', JobApplicationsView.as_view()),


]