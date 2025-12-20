from django.db import transaction
from .models import Application, ApplicationHistory
from notifications.tasks import send_candidate_email

VALID_TRANSITIONS = {
    'applied': ['screening', 'rejected'],
    'screening': ['interview', 'rejected'],
    'interview': ['offer', 'rejected'],
    'offer': ['hired', 'rejected'],
    'hired': [],
    'rejected': [],
}

def change_application_stage(application, new_stage, changed_by):
    current_stage = application.stage

    if new_stage not in VALID_TRANSITIONS[current_stage]:
        raise ValueError(
            f"Invalid stage transition from {current_stage} to {new_stage}"
        )

    with transaction.atomic():
        application.stage = new_stage
        application.save()

        ApplicationHistory.objects.create(
            application=application,
            from_stage=current_stage,
            to_stage=new_stage,
            changed_by=changed_by
        )

    # ✅ SEND EMAIL AFTER SUCCESSFUL COMMIT
    send_candidate_email.delay(
    "Application Status Update",
    f"Your application moved from {current_stage} to {new_stage}",
    application.candidate.email
    )


