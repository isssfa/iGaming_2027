from django.conf import settings
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from logs.utils import log_message
from security.permissions import ProtectedPostPermission
from coreconfig.service import email_service

from .models import AffiliateApplication
from .serializers import AffiliateApplicationSerializer


def _staff_notification_context(application, admin_url):
    """JSON-serializable context for the queued HTML email."""
    attachments = []
    for a in application.proof_attachments.all().order_by('sort_order', 'id'):
        attachments.append(
            {
                'label': a.label,
                'url': a.url or '',
                'file_display': a.file.name if a.file else '',
            }
        )
    return {
        'first_name': application.first_name,
        'last_name': application.last_name,
        'email': application.email,
        'phone': application.phone,
        'is_affiliate': application.is_affiliate,
        'traffic_sources': application.traffic_sources,
        'traffic_source_other_label': application.traffic_source_other_label,
        'traffic_source_details': application.traffic_source_details or {},
        'traffic_regions': application.traffic_regions,
        'traffic_volume': application.traffic_volume,
        'payment_preferences': application.payment_preferences,
        'payment_other_detail': application.payment_other_detail,
        'additional_notes': application.additional_notes,
        'proof_attachments': attachments,
        'application_id': application.pk,
        'created_at': application.created_at,
        'admin_url': admin_url,
    }


class AffiliateRegisterPageView(TemplateView):
    template_name = 'affiliates/register.html'


class AffiliateRegistrationView(APIView):
    permission_classes = [ProtectedPostPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    rate_limit = '5/m'

    def post(self, request):
        serializer = AffiliateApplicationSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            user = (
                getattr(request, 'user', None)
                if hasattr(request, 'user') and request.user.is_authenticated
                else None
            )
            log_message(
                'CRITICAL',
                f'Affiliate registration validation failed: {serializer.errors}',
                user=user,
                source_app='affiliates_AffiliateRegistrationView',
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save()
        application = AffiliateApplication.objects.prefetch_related(
            'proof_attachments',
        ).get(pk=application.pk)

        try:
            change_path = (
                f'/admin/affiliates/affiliateapplication/{application.id}/change/'
            )
            context = _staff_notification_context(
                application,
                request.build_absolute_uri(change_path),
            )
            email_queue = email_service.send_email_task(
                email_type='affiliate_new_application',
                subject=f'New affiliate application — {application.first_name} {application.last_name}',
                recipients=[settings.AFFILIATE_TICKETING_EMAIL],
                context=context,
                template_path='affiliates/email/new_application_staff.html',
                source_app='affiliates_AffiliateRegistrationView',
                related_model_id=application.id,
            )
            application.staff_notification_sent = email_queue is not None
            application.save(update_fields=['staff_notification_sent'])
        except Exception as e:
            user = (
                getattr(request, 'user', None)
                if hasattr(request, 'user') and request.user.is_authenticated
                else None
            )
            log_message(
                'ERROR',
                f'Failed to queue affiliate staff notification: {e}',
                user=user,
                source_app='affiliates_AffiliateRegistrationView_staff',
            )

        user = (
            getattr(request, 'user', None)
            if hasattr(request, 'user') and request.user.is_authenticated
            else None
        )
        log_message(
            'INFO',
            f'Affiliate application submitted: {application.id}',
            user=user,
            source_app='affiliates_AffiliateRegistrationView_ok',
        )
        return Response(
            {
                'message': (
                    'Thank you. Your application has been received. '
                    'We will review it and email you at the address you provided.'
                ),
                'id': application.id,
            },
            status=status.HTTP_201_CREATED,
        )
