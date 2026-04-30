from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Speaker, BecomeASpeaker
from .serializers import SpeakerSerializer, BecomeASpeakerSerializer
from logs.utils import log_message
from security.permissions import ProtectedPostPermission
from coreconfig.service import email_service

class SpeakerViewSet(APIView):
    """
    API endpoint to retrieve exhibition tiers and their associated options and images.
    Supports filtering by tier name.
    """
    # Public endpoint - no authentication required
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        name = request.data.get('name', None)
        company = request.data.get('company', None)
        role = request.data.get('role', None)

        # Prefetch related options and images to minimize database queries
        queryset = Speaker.objects.all()

        if name:
            queryset = queryset.filter(name__iexact=name)
        if company:
            queryset = queryset.filter(company__iexact=company)
        if role:
            queryset = queryset.filter(role__iexact=role)

        serializer = SpeakerSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class BecomeASpeakerView(APIView):
    """
    API endpoint to accept 'Become a Speaker' submissions.
    Sends email notification upon successful submission.
    """
    permission_classes = [ProtectedPostPermission]
    rate_limit = '10/m'  # 10 requests per minute

    def post(self, request):
        serializer = BecomeASpeakerSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save()
            
            # Queue email via RabbitMQ
            try:
                context = {
                    "first_name": submission.first_name,
                    "last_name": submission.last_name,
                    "email": submission.email,
                    "phone_number": submission.phone_number or "Not provided",
                    "linkedin_profile": submission.linkedin_profile or "Not provided",
                    "job_title": submission.job_title or "Not provided",
                    "company_name": submission.company_name or "Not provided",
                    "website_url": submission.website_url or "Not provided",
                    "company_type": submission.get_company_type_display() if submission.company_type else "Not provided",
                    "type_of_participation": submission.get_type_of_participation_display() if submission.type_of_participation else "Not provided",
                    "talk_title": submission.talk_title or "Not provided",
                    "topic_description": submission.topic_description or "Not provided",
                    "has_supporting_files": bool(submission.supporting_files),
                    "supporting_files_url": request.build_absolute_uri(submission.supporting_files.url) if submission.supporting_files else None,
                    "created_at": submission.created_at,
                }
                
                # Prepare attachments
                attachments = []
                if submission.supporting_files:
                    attachments.append(submission.supporting_files.path)
                
                email_queue = email_service.send_email_task(
                    email_type='speaker',
                    subject=f"🎤 New Speaker Submission - {submission.first_name} {submission.last_name}",
                    recipients=[settings.NOTIFICATION_EMAIL, "diana@igamingafrika.com"],
                    context=context,
                    template_path='speakers/email/become_speaker_notification.html',
                    attachments=attachments,
                    source_app='speakers_BecomeASpeakerView',
                    related_model_id=submission.id,
                )
                email_sent = email_queue is not None
            except Exception as e:
                user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
                log_message("ERROR", f"Failed to queue speaker submission email: {e}", user=user,
                            source_app='speakers_BecomeASpeakerView_1')
                email_sent = False

            submission.email_sent = email_sent
            submission.save(update_fields=['email_sent'])

            user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
            log_message("INFO", f"Speaker submission received from {submission.first_name} {submission.last_name}", 
                       user=user, source_app='speakers_BecomeASpeakerView_2')
            
            return Response(
                {"message": "Speaker submission received successfully."}, 
                status=status.HTTP_201_CREATED
            )

        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        log_message("CRITICAL", f"Speaker submission validation failed: {serializer.errors}", 
                   user=user, source_app='speakers_BecomeASpeakerView_3')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)