from django.urls import path

from .views import AffiliateRegistrationView

urlpatterns = [
    path('register/', AffiliateRegistrationView.as_view(), name='affiliate-register'),
]
