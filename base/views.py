from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from logs.utils import log_message
from security.permissions import ProtectedPostPermission
from coreconfig.service import email_service
from .serializers import EventRegistrationSerializer, InquirySerializer


class EventRegistrationView(APIView):
    # No authentication required - uses CSRF token instead
    permission_classes = [ProtectedPostPermission]
    rate_limit = '10/m'  # 10 requests per minute

    def post(self, request):
        serializer = EventRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            registration = serializer.save()
            # Set user if authenticated
            if hasattr(request, 'user') and request.user.is_authenticated:
                registration.user = request.user
                registration.save(update_fields=['user'])

            # Queue email via RabbitMQ
            try:
                context = {
                    "first_name": registration.first_name,
                    "last_name": registration.last_name,
                    "company_name": registration.company_name,
                    "work_email": registration.work_email,
                    "phone_number": registration.phone_number,
                    "interests": registration.interests,
                    "created_at": registration.created_at,
                }
                email_queue = email_service.send_email_task(
                    email_type='registration',
                    subject=f"📬 New Event Registration Received - {registration.first_name}",
                    recipients=[settings.NOTIFICATION_EMAIL],
                    context=context,
                    template_path='email/registration_notification.html',
                    source_app='base_EventRegistrationView',
                    related_model_id=registration.id,
                )
                email_sent = email_queue is not None
            except Exception as e:
                user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
                log_message("ERROR", f"Failed to queue email: {e}", user=user,
                            source_app='base_EventRegistrationView_1')
                email_sent = False

            registration.email_sent = email_sent
            registration.save(update_fields=['email_sent'])

            # Get user if authenticated, otherwise use None
            user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
            log_message("INFO", f"Registration successful.", user=user,
                        source_app='base_EventRegistrationView_2')
            return Response({"message": "Registration successful."}, status=status.HTTP_201_CREATED)

        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        log_message("CRITICAL", f"{serializer.errors}", user=user, source_app='base_EventRegistrationView_3')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InquiryView(APIView):
    # No authentication required - uses CSRF token instead
    permission_classes = [ProtectedPostPermission]
    rate_limit = '10/m'  # 10 requests per minute

    def post(self, request):
        serializer = InquirySerializer(data=request.data)
        if serializer.is_valid():
            inquiry = serializer.save()

            # Queue email via RabbitMQ
            try:
                plain_body = f"From: {inquiry.name} <{inquiry.email}>\n\n{inquiry.message}"
                email_queue = email_service.send_email_task(
                    email_type='inquiry',
                    subject=f"New Inquiry: {inquiry.topic}",
                    recipients=[settings.NOTIFICATION_EMAIL],
                    plain_body=plain_body,
                    source_app='base_InquiryView',
                    related_model_id=inquiry.id,
                )
                email_sent = email_queue is not None
            except Exception as e:
                user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
                log_message("ERROR", f"Failed to queue inquiry email: {e}", user=user, source_app='base_InquiryView_1')
                email_sent = False

            inquiry.email_sent = email_sent
            inquiry.save(update_fields=['email_sent'])
            user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
            log_message("INFO", f"Inquiry submitted successfully.", user=user, source_app='base_InquiryView_2')
            return Response({"message": "Inquiry submitted successfully."}, status=status.HTTP_201_CREATED)

        user = getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        log_message("CRITICAL", f"{serializer.errors}", user=user, source_app='base_InquiryView_3')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

