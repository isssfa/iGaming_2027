from django.urls import path
from .views import SponsorListAPIView

urlpatterns = [
    path('', SponsorListAPIView.as_view(), name='sponsors'),
]
