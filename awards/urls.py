from django.urls import path

from .views import AwardsCategoryListAPIView, VoteConfirmationView, VoteSubmissionAPIView

urlpatterns = [
    path('categories/', AwardsCategoryListAPIView.as_view(), name='awards-categories'),
    path('votes/', VoteSubmissionAPIView.as_view(), name='awards-vote-submit'),
    path('votes/confirm/', VoteConfirmationView.as_view(), name='awards-vote-confirm'),
]

