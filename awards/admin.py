import csv

from django.contrib import admin, messages
from django.db.models import Case, Count, IntegerField, Sum, When
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from coreconfig.service import email_service

from .models import Category, Nominee, Vote
from .utils import build_confirmation_url, vote_rows_for_queue_context


def _vote_summary_queryset():
    return (
        Vote.objects.values(
            'category__id',
            'category__title',
            'nominee__id',
            'nominee__nominee',
        )
        .annotate(
            confirmed_votes=Sum(
                Case(
                    When(is_confirmed=True, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            unconfirmed_votes=Sum(
                Case(
                    When(is_confirmed=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            ),
            total_votes=Count('id'),
        )
        .order_by('category__title', 'nominee__nominee')
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'priority', 'added_on', 'updated_on', 'added_by']
    list_editable = ['priority']
    search_fields = ['title', 'description']
    ordering = ['priority', 'title']
    readonly_fields = ['added_on', 'updated_on', 'added_by']

    def save_model(self, request, obj, form, change):
        if not obj.added_by and request.user.is_authenticated:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    list_display = ['id', 'nominee', 'category', 'added_on', 'updated_on', 'added_by']
    list_filter = ['category']
    search_fields = ['nominee', 'category__title']
    autocomplete_fields = ['category']
    readonly_fields = ['added_on', 'updated_on', 'added_by']

    def save_model(self, request, obj, form, change):
        if not obj.added_by and request.user.is_authenticated:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    change_list_template = 'admin/awards/vote_change_list.html'
    list_display = [
        'id',
        'voter_name',
        'voter_email',
        'company',
        'position',
        'category',
        'nominee',
        'is_confirmed',
        'email_sent',
        'created_at',
        'confirmed_at',
        'resend_button',
    ]
    list_filter = ['is_confirmed', 'email_sent', 'category', 'created_at']
    search_fields = [
        'voter_name',
        'voter_email',
        'company',
        'position',
        'category__title',
        'nominee__nominee',
    ]
    readonly_fields = ['created_at', 'confirmed_at', 'batch_id', 'confirmation_token']
    actions = ['resend_confirmation_email_action']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'summary/export/',
                self.admin_site.admin_view(self.summary_export_view),
                name='awards_vote_summary_export',
            ),
            path(
                'summary/',
                self.admin_site.admin_view(self.summary_view),
                name='awards_vote_summary',
            ),
            path(
                '<int:vote_id>/resend-confirmation/',
                self.admin_site.admin_view(self.resend_confirmation_view),
                name='awards_vote_resend_confirmation',
            ),
        ]
        return custom_urls + urls

    def _queue_vote_confirmation_email(self, vote_obj, request=None):
        pending_votes = list(
            Vote.objects.select_related('category', 'nominee').filter(
                voter_email=vote_obj.voter_email,
                confirmation_token=vote_obj.confirmation_token,
                is_confirmed=False,
            )
        )
        if not pending_votes:
            return False

        confirm_url = build_confirmation_url(
            token=vote_obj.confirmation_token,
            email=vote_obj.voter_email,
            request=request,
        )
        vote_rows = vote_rows_for_queue_context(pending_votes)
        email_queue = email_service.send_email_task(
            email_type='awards_vote',
            subject='Confirm Your iGaming Awards Vote',
            recipients=[vote_obj.voter_email],
            context={
                "voter_name": vote_obj.voter_name,
                "vote_rows": vote_rows,
                "confirm_url": confirm_url,
            },
            template_path='awards/email/vote_confirmation.html',
            source_app='awards_VoteAdmin',
            related_model_id=vote_obj.id,
        )
        Vote.objects.filter(
            id__in=[v.id for v in pending_votes]
        ).update(email_sent=email_queue is not None)
        return email_queue is not None

    def resend_button(self, obj):
        if obj.is_confirmed:
            return '-'
        return format_html(
            '<a class="button" href="{}">Resend Email</a>',
            f'/admin/awards/vote/{obj.id}/resend-confirmation/',
        )

    resend_button.short_description = 'Actions'

    def resend_confirmation_view(self, request, vote_id):
        try:
            vote = Vote.objects.get(id=vote_id)
            if vote.is_confirmed:
                messages.warning(request, "Vote is already confirmed.")
            else:
                ok = self._queue_vote_confirmation_email(vote, request=request)
                if ok:
                    messages.success(request, "Confirmation email queued successfully.")
                else:
                    messages.error(request, "Failed to queue confirmation email.")
        except Vote.DoesNotExist:
            messages.error(request, "Vote not found.")
        return redirect('admin:awards_vote_changelist')

    def resend_confirmation_email_action(self, request, queryset):
        count = 0
        for vote in queryset.filter(is_confirmed=False):
            if self._queue_vote_confirmation_email(vote, request=request):
                count += 1
        self.message_user(request, f"{count} confirmation email(s) queued.")

    resend_confirmation_email_action.short_description = "Resend confirmation email(s)"

    def summary_view(self, request):
        summary = _vote_summary_queryset()
        context = dict(
            self.admin_site.each_context(request),
            title='Awards Vote Summary',
            summary=summary,
        )
        return render(request, 'admin/awards/vote_summary.html', context)

    def summary_export_view(self, request):
        summary = _vote_summary_queryset()
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="awards_vote_summary.csv"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(
            [
                'category_id',
                'category_title',
                'nominee_id',
                'nominee_name',
                'confirmed_votes',
                'unconfirmed_votes',
                'total_votes',
            ]
        )
        for row in summary:
            writer.writerow(
                [
                    row['category__id'],
                    row['category__title'],
                    row['nominee__id'],
                    row['nominee__nominee'],
                    row['confirmed_votes'] or 0,
                    row['unconfirmed_votes'] or 0,
                    row['total_votes'] or 0,
                ]
            )
        return response

