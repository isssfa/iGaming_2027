import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from coreconfig.service import email_service
from security.permissions import ProtectedPostPermission

from .models import Category, Nominee, Vote
from .serializers import CategoryWithNomineesSerializer, VoteSubmissionSerializer
from .utils import build_confirmation_url, vote_rows_for_queue_context


class AwardsCategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.prefetch_related(
            Prefetch('nominees', queryset=Nominee.objects.order_by('nominee'))
        ).order_by('priority', 'title')
        serializer = CategoryWithNomineesSerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VoteSubmissionAPIView(APIView):
    permission_classes = [ProtectedPostPermission]
    rate_limit = '10/m'

    def post(self, request):
        serializer = VoteSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        voter_name = data['voter_name'].strip()
        voter_email = data['voter_email'].strip().lower()
        company = (data.get('company') or '').strip()
        position = (data.get('position') or '').strip()
        votes_payload = data['votes']
        category_ids = [item['category_obj'].id for item in votes_payload]

        confirmed_already = list(
            Vote.objects.filter(
                voter_email=voter_email,
                category_id__in=category_ids,
                is_confirmed=True,
            )
            .values_list('category__title', flat=True)
            .distinct()
        )
        if confirmed_already:
            return Response(
                {
                    "message": (
                        "You have already voted in the following category or categories. "
                        "Your submission was not accepted."
                    ),
                    "categories": confirmed_already,
                    "error": "already_voted_in_category",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = uuid.uuid4().hex
        batch_id = uuid.uuid4()
        created_votes = []

        with transaction.atomic():
            Vote.objects.filter(
                voter_email=voter_email,
                category_id__in=category_ids,
                is_confirmed=False,
            ).delete()

            for vote_item in votes_payload:
                created_votes.append(
                    Vote(
                        voter_name=voter_name,
                        voter_email=voter_email,
                        company=company,
                        position=position,
                        category=vote_item['category_obj'],
                        nominee=vote_item['nominee_obj'],
                        batch_id=batch_id,
                        confirmation_token=token,
                    )
                )
            Vote.objects.bulk_create(created_votes)

        created_votes = list(
            Vote.objects.filter(batch_id=batch_id).select_related('category', 'nominee')
        )
        confirm_url = build_confirmation_url(token=token, email=voter_email, request=request)
        vote_rows = vote_rows_for_queue_context(created_votes)

        email_queue = email_service.send_email_task(
            email_type='awards_vote',
            subject='Confirm Your iGaming Awards Vote',
            recipients=[voter_email],
            context={
                "voter_name": voter_name,
                "vote_rows": vote_rows,
                "confirm_url": confirm_url,
            },
            template_path='awards/email/vote_confirmation.html',
            source_app='awards_VoteSubmissionAPIView',
            related_model_id=created_votes[0].id if created_votes else None,
        )

        email_sent = email_queue is not None
        Vote.objects.filter(batch_id=batch_id).update(email_sent=email_sent)

        return Response(
            {
                "message": "Vote received. Please confirm from your email to finalize.",
                "email_sent": email_sent,
            },
            status=status.HTTP_201_CREATED,
        )


class VoteConfirmationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.GET.get('token', '').strip()
        email = request.GET.get('email', '').strip().lower()

        if not token or not email:
            return HttpResponseBadRequest("Missing confirmation token or email.")

        pending_votes = list(
            Vote.objects.select_related('category', 'nominee').filter(
                confirmation_token=token,
                voter_email=email,
                is_confirmed=False,
            )
        )

        if pending_votes:
            now = timezone.now()
            Vote.objects.filter(id__in=[v.id for v in pending_votes]).update(
                is_confirmed=True,
                confirmed_at=now,
            )
            return render(
                request,
                'awards/vote_confirmation_result.html',
                {
                    "status_text": "confirmed",
                    "voter_email": email,
                    "votes": pending_votes,
                },
            )

        confirmed_votes = list(
            Vote.objects.select_related('category', 'nominee').filter(
                confirmation_token=token,
                voter_email=email,
                is_confirmed=True,
            )
        )
        return render(
            request,
            'awards/vote_confirmation_result.html',
            {
                "status_text": "already_confirmed" if confirmed_votes else "invalid",
                "voter_email": email,
                "votes": confirmed_votes,
                "support_email": getattr(settings, 'NOTIFICATION_EMAIL', ''),
            },
        )

