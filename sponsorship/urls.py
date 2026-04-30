from django.urls import path
from .views import SponsorshipListAPIView

urlpatterns = [
    path('', SponsorshipListAPIView.as_view(), name='sponsorships'),
]
